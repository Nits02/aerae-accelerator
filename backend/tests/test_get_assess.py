import json
import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.db import AssessmentJob, engine
from app.main import app

client = TestClient(app)

DUMMY_RESULT = {
    "risks": [{"category": "Data Privacy", "severity": "high", "reason": "PII exposed"}],
    "trust_score": 75,
    "opa_result": {"allow": True, "deny_reasons": []},
}


def test_get_completed_job():
    """Insert a completed job and assert GET returns 200 with the full result."""
    job_id = uuid.uuid4()
    job = AssessmentJob(
        id=job_id,
        status="Complete",
        result_json=json.dumps(DUMMY_RESULT),
    )
    with Session(engine) as session:
        session.add(job)
        session.commit()

    response = client.get(f"/api/v1/assess/{job_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["job_id"] == str(job_id)
    assert data["status"] == "Complete"
    assert data["result"]["trust_score"] == 75
    assert data["result"]["risks"][0]["severity"] == "high"
    assert data["result"]["opa_result"]["allow"] is True


def test_get_nonexistent_job_returns_404():
    """GET with a random UUID that doesn't exist should return 404."""
    response = client.get(f"/api/v1/assess/{uuid.uuid4()}")
    assert response.status_code == 404


def test_get_processing_job_returns_202():
    """A job still processing should return 202 Accepted."""
    job_id = uuid.uuid4()
    job = AssessmentJob(id=job_id, status="Processing")
    with Session(engine) as session:
        session.add(job)
        session.commit()

    response = client.get(f"/api/v1/assess/{job_id}")
    assert response.status_code == 202
    assert response.json()["status"] == "Processing"
