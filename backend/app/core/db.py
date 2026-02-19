from __future__ import annotations

import uuid
from typing import Optional

from sqlmodel import Field, SQLModel, create_engine

from app.core.config import settings


# ── Models ───────────────────────────────────────────────────
class AssessmentJob(SQLModel, table=True):
    """Tracks an assessment job and its result."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    status: str = Field(default="pending")
    result_json: Optional[str] = Field(default=None)

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
