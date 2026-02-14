from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the root-level .env file (three levels up from core/config.py)
ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    """Application settings loaded securely from the root-level .env file."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    APP_NAME: str = "AERAE Accelerator"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./aerae_local.db"

    # ── Azure OpenAI ─────────────────────────────────────────
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = "https://ai-proxy.lab.epam.com"
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4o-mini-2024-07-18"

    # ── Google Gemini ────────────────────────────────────────
    GEMINI_API_KEY: str = ""

    # ── ChromaDB ─────────────────────────────────────────────
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_data"


settings = Settings()
