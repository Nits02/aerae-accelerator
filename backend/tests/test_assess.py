import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_assess_returns_200_with_uuid():
    """POST /api/v1/assess should return 200 immediately with a valid UUID job ID."""
    with patch("app.main.run_assessment") as mock_bg:
        response = client.post(
            "/api/v1/assess",
            json={"pdf_path": "/tmp/fake.pdf", "github_url": "https://github.com/owner/repo"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Processing"

    # Validate that job_id is a proper UUID
    job_uuid = uuid.UUID(data["job_id"])
    assert str(job_uuid) == data["job_id"]

    # Background task should NOT have been awaited; it's only scheduled
    mock_bg.assert_called_once()
