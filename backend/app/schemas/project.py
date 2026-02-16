"""Pydantic schemas for project artifacts – unifying PDF and Git data."""

from pydantic import BaseModel, Field


class ProjectArtifact(BaseModel):
    """Unified representation of a project ingested from PDFs and/or Git repos.

    Attributes
    ----------
    project_name : str
        Human-readable name of the project.
    source_url : str
        URL of the source (GitHub repo URL, document link, etc.).
    document_text : str | None
        Extracted text content from a PDF or other document.
        ``None`` when no document has been ingested.
    code_metadata : dict
        Metadata extracted from the code repository, e.g.::

            {
                "languages": ["Python", "TypeScript"],
                "files_count": 42,
                "secrets_found": 0,
                "findings": [],
            }

        Defaults to an empty dict when no repo has been scanned.
    """

    project_name: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Human-readable name of the project",
        examples=["AERAE Accelerator"],
    )
    source_url: str = Field(
        ...,
        min_length=1,
        description="URL of the source (GitHub repo, document link, etc.)",
        examples=["https://github.com/owner/repo"],
    )
    document_text: str | None = Field(
        default=None,
        description="Extracted text content from a PDF or other document",
    )
    code_metadata: dict = Field(
        default_factory=dict,
        description="Metadata extracted from the code repository",
        examples=[{"languages": ["Python"], "files_count": 10, "secrets_found": 0}],
    )
