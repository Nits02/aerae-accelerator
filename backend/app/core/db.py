from sqlmodel import SQLModel, create_engine

from app.core.config import settings

# SQLite requires check_same_thread=False for FastAPI's async usage
connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=connect_args,
)


def create_db_and_tables() -> None:
    """Create all tables registered with SQLModel.metadata."""
    SQLModel.metadata.create_all(engine)
