from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.config import settings
from app.core.db import create_db_and_tables


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

# ── Routers ──────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["health"])
async def health_check():
    """Lightweight liveness probe."""
    return {"status": "ok"}
