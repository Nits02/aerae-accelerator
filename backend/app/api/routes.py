from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["v1"])


# ── Request / Response schemas ───────────────────────────────
class PromptRequest(BaseModel):
    prompt: str
    model: str | None = None


class GenerateResponse(BaseModel):
    source: str
    model: str
    response: str


# ── Root ─────────────────────────────────────────────────────
@router.get("/")
async def root():
    return {"message": "AERAE Accelerator API v1"}


# ── Gemini endpoint ─────────────────────────────────────────
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


# ── Azure OpenAI endpoint ───────────────────────────────────
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
