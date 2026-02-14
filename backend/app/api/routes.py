import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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
