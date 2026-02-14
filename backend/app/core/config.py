from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "AERAE Accelerator"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./aerae.db"

    # Azure OpenAI
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"

    # Google Gemini
    GOOGLE_API_KEY: str = ""

    # ChromaDB
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_data"

    class Config:
        env_file = ".env"


settings = Settings()
