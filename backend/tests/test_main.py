from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── Health ───────────────────────────────────────────────────
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── Gemini endpoint ─────────────────────────────────────────
@patch("app.services.gemini_service.generate_content", return_value="mocked gemini reply")
def test_generate_gemini(mock_gen):
    response = client.post(
        "/api/v1/generate/gemini",
        json={"prompt": "Hello Gemini"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "gemini"
    assert data["response"] == "mocked gemini reply"


# ── Azure OpenAI endpoint ───────────────────────────────────
@patch("app.services.azure_openai_service.chat_completion", return_value="mocked azure reply")
def test_generate_azure_openai(mock_chat):
    response = client.post(
        "/api/v1/generate/azure-openai",
        json={"prompt": "Hello Azure"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "azure-openai"
    assert data["response"] == "mocked azure reply"
