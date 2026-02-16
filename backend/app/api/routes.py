import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.schemas.project import ProjectArtifact

router = APIRouter(tags=["v1"])
logger = logging.getLogger(__name__)


# ── Request / Response schemas ───────────────────────────────
class PromptRequest(BaseModel):
    prompt: str
    model: str | None = None


class GenerateResponse(BaseModel):
    source: str
    model: str
    response: str
    fallback_used: bool = False
    fallback_reason: str | None = None


# ── Root ─────────────────────────────────────────────────────
@router.get("/")
async def root():
    return {"message": "AERAE Accelerator API v1"}


# ── Unified endpoint (Gemini → Azure OpenAI fallback) ───────
@router.post("/generate", response_model=GenerateResponse)
async def generate(body: PromptRequest):
    """Generate content using Gemini first; fall back to Azure OpenAI on failure."""
    # --- Try Gemini first ---
    try:
        from app.services.gemini_service import generate_content, DEFAULT_MODEL

        text = generate_content(body.prompt, model=body.model)
        return GenerateResponse(
            source="gemini",
            model=body.model or DEFAULT_MODEL,
            response=text,
        )
    except Exception as gemini_exc:
        gemini_error = str(gemini_exc)
        logger.warning("Gemini failed (%s), falling back to Azure OpenAI", gemini_error)

    # --- Fallback to Azure OpenAI ---
    try:
        from app.services.azure_openai_service import chat_completion, DEFAULT_DEPLOYMENT

        text = chat_completion(body.prompt, deployment=body.model)
        return GenerateResponse(
            source="azure-openai",
            model=body.model or DEFAULT_DEPLOYMENT,
            response=text,
            fallback_used=True,
            fallback_reason=f"Gemini unavailable: {gemini_error}",
        )
    except Exception as azure_exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Both providers failed. "
                f"Gemini: {gemini_error} | Azure OpenAI: {azure_exc}"
            ),
        )


# ── Gemini endpoint (direct) ────────────────────────────────
@router.post("/generate/gemini", response_model=GenerateResponse)
async def generate_gemini(body: PromptRequest):
    """Generate content using Google Gemini."""
    try:
        from app.services.gemini_service import generate_content, DEFAULT_MODEL

        text = generate_content(body.prompt, model=body.model)
        return GenerateResponse(
            source="gemini",
            model=body.model or DEFAULT_MODEL,
            response=text,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini error: {exc}")


# ── Azure OpenAI endpoint (direct) ──────────────────────────
@router.post("/generate/azure-openai", response_model=GenerateResponse)
async def generate_azure_openai(body: PromptRequest):
    """Generate content using Azure OpenAI (EPAM DIAL proxy)."""
    try:
        from app.services.azure_openai_service import chat_completion, DEFAULT_DEPLOYMENT

        text = chat_completion(body.prompt, deployment=body.model)
        return GenerateResponse(
            source="azure-openai",
            model=body.model or DEFAULT_DEPLOYMENT,
            response=text,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Azure OpenAI error: {exc}")


# ── Ingest endpoint (PDF + Git → ProjectArtifact) ───────────
@router.post("/ingest", response_model=ProjectArtifact)
async def ingest(
    github_url: str = Form(..., description="HTTPS URL of the public GitHub repository"),
    project_name: str = Form(None, description="Project name (derived from repo URL if omitted)"),
    pdf: UploadFile | None = File(None, description="Optional PDF document to analyse"),
):
    """Ingest a project from a GitHub repo and an optional PDF document.

    1. Clones the repo, lists files, and runs Gitleaks secret scanning.
    2. If a PDF is uploaded, extracts project purpose / data types / risks.
    3. Merges everything into a :class:`ProjectArtifact` and returns it.
    """
    from app.services.git_scanner import (
        clone_repo_context,
        list_files,
        scan_secrets,
    )

    # ── Derive project name from URL if not provided ─────────
    if not project_name:
        # e.g. "https://github.com/owner/repo.git" → "repo"
        project_name = github_url.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")

    # ── Git scanning ─────────────────────────────────────────
    code_metadata: dict = {}
    try:
        with clone_repo_context(github_url) as (dir_path, repo):
            files = list_files(dir_path)
            code_metadata["files"] = files
            code_metadata["files_count"] = len(files)

            # Detect predominant extensions / languages
            extensions: dict[str, int] = {}
            for f in files:
                ext = Path(f).suffix
                if ext:
                    extensions[ext] = extensions.get(ext, 0) + 1
            code_metadata["extensions"] = extensions

            # Secret scanning
            try:
                secrets_result = scan_secrets(dir_path)
                code_metadata["secrets_found"] = secrets_result["secrets_found"]
                code_metadata["secret_scan_successful"] = secrets_result["scan_successful"]
                code_metadata["secret_findings"] = secrets_result["findings"]
            except FileNotFoundError:
                logger.warning("Gitleaks not installed – skipping secret scan")
                code_metadata["secrets_found"] = None
                code_metadata["secret_scan_successful"] = False
                code_metadata["secret_findings"] = []
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=f"Git scanning failed: {exc}")

    # ── PDF parsing (optional) ───────────────────────────────
    document_text: str | None = None
    if pdf is not None:
        if not pdf.filename or not pdf.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=422, detail="Uploaded file must be a PDF")

        # Write the upload to a temp file so parse_pdf can read it
        try:
            from app.services.pdf_parser import parse_pdf

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(await pdf.read())
                tmp_path = tmp.name

            try:
                pdf_result = parse_pdf(tmp_path)
                # Flatten PDF extraction into a readable summary
                document_text = (
                    f"Purpose: {pdf_result.get('project_purpose', 'N/A')}\n"
                    f"Data types: {', '.join(pdf_result.get('data_types_used', []))}\n"
                    f"Risks: {', '.join(pdf_result.get('potential_risks', []))}"
                )
                code_metadata["pdf_analysis"] = {
                    "project_purpose": pdf_result.get("project_purpose"),
                    "data_types_used": pdf_result.get("data_types_used"),
                    "potential_risks": pdf_result.get("potential_risks"),
                    "ai_source": pdf_result.get("source"),
                    "fallback_used": pdf_result.get("fallback_used"),
                }
            finally:
                Path(tmp_path).unlink(missing_ok=True)

        except RuntimeError as exc:
            logger.error("PDF parsing failed: %s", exc)
            raise HTTPException(status_code=502, detail=f"PDF parsing failed: {exc}")

    return ProjectArtifact(
        project_name=project_name,
        source_url=github_url,
        document_text=document_text,
        code_metadata=code_metadata,
    )
