import json
import logging
import uuid as uuid_mod
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel import Session

from app.api.routes import router as api_router
from app.core.config import settings
from app.core.db import AssessmentJob, create_db_and_tables, engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables. Shutdown: cleanup (if needed)."""
    create_db_and_tables()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for the AERAE Accelerator platform",
    version="0.1.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# ── CORS (allow frontend dev server) ─────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["health"])
async def health_check():
    """Lightweight liveness probe."""
    return {"status": "ok"}


# ── Assessment endpoint ──────────────────────────────────────
class AssessRequest(BaseModel):
    pdf_path: str
    github_url: str


class AssessResponse(BaseModel):
    job_id: str
    status: str


@app.post("/api/v1/assess", response_model=AssessResponse, tags=["assess"])
async def assess(body: AssessRequest, background_tasks: BackgroundTasks):
    """Start an assessment job.

    Creates a DB record with *Processing* status, kicks off a background
    pipeline, and returns the job UUID immediately.
    """
    job = AssessmentJob(status="Processing")
    with Session(engine) as session:
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = str(job.id)

    background_tasks.add_task(run_assessment, job_id, body.pdf_path, body.github_url)
    return AssessResponse(job_id=job_id, status="Processing")


@app.get("/api/v1/assess/{job_id}", tags=["assess"])
async def get_assess(job_id: str):
    """Poll the status of an assessment job.

    - **202 Accepted** – job is still processing.
    - **200 OK** – job is complete; body contains the full result.
    - **404 Not Found** – no job with this UUID exists.
    """
    try:
        uid = uuid_mod.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid job ID")

    with Session(engine) as session:
        job = session.get(AssessmentJob, uid)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status == "Processing":
        return JSONResponse(
            status_code=202,
            content={"job_id": job_id, "status": "Processing"},
        )

    # Complete or Failed – return the stored result
    result = json.loads(job.result_json) if job.result_json else {}
    return JSONResponse(
        status_code=200,
        content={
            "job_id": job_id,
            "status": job.status,
            "result": result,
        },
    )
async def run_assessment(job_id: str, pdf_path: str, github_url: str) -> None:
    """Execute the full assessment pipeline in the background.

    Phases
    ------
    1. **Ingestion** – GitScanner (clone + list files), Gitleaks (secret scan),
       PDF parser (Azure OpenAI → Gemini fallback).
    2. **RAG** – AzureAIEngine.get_embedding → PolicyVectorStore.search →
       AzureAIEngine.analyze_risk.
    3. **Scoring** – calculate_trust_score.
    4. **OPA** – OPAGatekeeper.evaluate_payload.
    """
    from app.core.scoring import calculate_trust_score
    from app.services.ai_engine import AzureAIEngine
    from app.services.git_scanner import clone_repo_context, list_files, scan_secrets
    from app.services.opa_client import OPAGatekeeper
    from app.services.pdf_parser import parse_pdf
    from app.services.vector_store import PolicyVectorStore

    try:
        # ── Phase 1: Ingestion ───────────────────────────────

        # 1a. Git clone, file listing, and secret scanning
        code_metadata: dict = {}
        with clone_repo_context(github_url) as (dir_path, _repo):
            files = list_files(dir_path)
            code_metadata["files"] = files
            code_metadata["files_count"] = len(files)

            # Detect predominant extensions
            extensions: dict[str, int] = {}
            for f in files:
                ext = Path(f).suffix
                if ext:
                    extensions[ext] = extensions.get(ext, 0) + 1
            code_metadata["extensions"] = extensions

            # 1b. Gitleaks secret scanning
            secrets_result = scan_secrets(dir_path)
            code_metadata["secrets_found"] = secrets_result["secrets_found"]
            code_metadata["secret_scan_successful"] = secrets_result["scan_successful"]
            code_metadata["secret_findings"] = secrets_result["findings"]

        # 1c. PDF parsing (Azure OpenAI → Gemini fallback)
        pdf_result = parse_pdf(pdf_path)

        # Build a textual summary for embedding
        project_description = (
            f"Project from {github_url}. "
            f"Purpose: {pdf_result.get('project_purpose', 'N/A')}. "
            f"Data types: {', '.join(pdf_result.get('data_types_used', []))}. "
            f"Files: {code_metadata['files_count']}. "
            f"Secrets found: {code_metadata['secrets_found']}."
        )

        # ── Phase 2: RAG ─────────────────────────────────────
        ai_engine = AzureAIEngine()

        # 2a. Generate embedding for the project description
        embedding = await ai_engine.get_embedding(project_description)

        # 2b. Search the policy vector store for relevant policies
        vector_store = PolicyVectorStore(
            persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
        )
        policy_hits = vector_store.search(query_embedding=embedding)
        if not policy_hits:
            logger.warning(
                "No relevant policies retrieved from the vector store. "
                "Ensure the database has been seeded. "
                "Proceeding with LLM analysis without policy grounding."
            )
        policies = [h["document"] for h in policy_hits]

        # 2c. Analyse risk using the AI engine
        project_json = {
            "github_url": github_url,
            "code_metadata": code_metadata,
            "pdf_analysis": pdf_result,
        }
        risk_result = await ai_engine.analyze_risk(project_json, policies)
        risks = risk_result.get("risks", [])

        # ── Phase 3: Scoring ─────────────────────────────────
        trust_score = calculate_trust_score(
            risks,
            code_metadata.get("secrets_found", 0),
        )

        # ── Phase 4: OPA ─────────────────────────────────────
        opa = OPAGatekeeper()
        opa_payload = {
            "trust_score": trust_score,
            "risks": risks,
            "secrets_count": code_metadata.get("secrets_found", 0),
        }
        opa_result = await opa.evaluate_payload(opa_payload)

        # ── Persist final result ─────────────────────────────
        final_result = {
            "github_url": github_url,
            "pdf_path": pdf_path,
            "code_metadata": code_metadata,
            "pdf_analysis": pdf_result,
            "policies_matched": policies,
            "risks": risks,
            "trust_score": trust_score,
            "opa_result": opa_result,
        }

        with Session(engine) as session:
            job = session.get(AssessmentJob, uuid_mod.UUID(job_id))
            if job:
                job.status = "Complete"
                job.result_json = json.dumps(final_result, default=str)
                session.add(job)
                session.commit()

    except Exception as exc:
        logger.exception("Assessment job %s failed", job_id)
        with Session(engine) as session:
            job = session.get(AssessmentJob, uuid_mod.UUID(job_id))
            if job:
                job.status = "Failed"
                job.result_json = json.dumps({"error": str(exc)})
                session.add(job)
                session.commit()
