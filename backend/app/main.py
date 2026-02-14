from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for the AERAE Accelerator platform",
    version="0.1.0",
    debug=settings.DEBUG,
)

# ── Routers ──────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["health"])
async def health_check():
    """Lightweight liveness probe."""
    return {"status": "ok"}
