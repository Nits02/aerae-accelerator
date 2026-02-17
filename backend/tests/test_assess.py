import logging
import uuid
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.db import AssessmentJob, engine
from app.main import app, run_assessment

client = TestClient(app)


def test_assess_returns_200_with_uuid():
    """POST /api/v1/assess should return 200 immediately with a valid UUID job ID."""
    with patch("app.main.run_assessment") as mock_bg:
        response = client.post(
            "/api/v1/assess",
            data={"github_url": "https://github.com/owner/repo"},
            files={"pdf": ("fake.pdf", b"%PDF-1.4 fake content", "application/pdf")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Processing"

    # Validate that job_id is a proper UUID
    job_uuid = uuid.UUID(data["job_id"])
    assert str(job_uuid) == data["job_id"]

    # Background task should NOT have been awaited; it's only scheduled
    mock_bg.assert_called_once()


@pytest.mark.asyncio
async def test_empty_vector_store_emits_warning(caplog):
    """When PolicyVectorStore.search returns [], a warning should be logged."""
    # Create a real job in the DB so run_assessment can update it
    job_id = uuid.uuid4()
    job = AssessmentJob(id=job_id, status="Processing")
    with Session(engine) as session:
        session.add(job)
        session.commit()

    # ── Mock all external dependencies ───────────────────────
    @contextmanager
    def fake_clone_ctx(url):
        yield "/tmp/fake_repo", MagicMock()

    mock_scan = {
        "secrets_found": 0,
        "findings": [],
        "scan_successful": True,
        "error": None,
    }

    mock_pdf = {
        "project_purpose": "Test project",
        "data_types_used": ["text"],
        "potential_risks": [],
        "source": "azure-openai",
        "fallback_used": False,
        "fallback_reason": None,
    }

    mock_engine_instance = MagicMock()
    mock_engine_instance.get_embedding = AsyncMock(return_value=[0.1] * 1536)
    mock_engine_instance.analyze_risk = AsyncMock(return_value={"risks": []})

    mock_store_instance = MagicMock()
    mock_store_instance.search.return_value = []  # ← empty vector store

    mock_opa_instance = MagicMock()
    mock_opa_instance.evaluate_payload = AsyncMock(
        return_value={"allow": True, "deny_reasons": []}
    )

    with (
        patch("app.services.git_scanner.clone_repo_context", side_effect=fake_clone_ctx),
        patch("app.services.git_scanner.list_files", return_value=["README.md"]),
        patch("app.services.git_scanner.scan_secrets", return_value=mock_scan),
        patch("app.services.pdf_parser.parse_pdf", return_value=mock_pdf),
        patch("app.services.ai_engine.AzureAIEngine", return_value=mock_engine_instance),
        patch("app.services.vector_store.PolicyVectorStore", return_value=mock_store_instance),
        patch("app.services.opa_client.OPAGatekeeper", return_value=mock_opa_instance),
        caplog.at_level(logging.WARNING, logger="app.main"),
    ):
        await run_assessment(str(job_id), "/tmp/fake.pdf", "https://github.com/owner/repo")

    assert "No relevant policies retrieved from the vector store" in caplog.text
