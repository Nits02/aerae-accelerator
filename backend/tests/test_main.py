from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── Health ───────────────────────────────────────────────────
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── Unified /generate (Gemini succeeds) ─────────────────────
@patch("app.services.gemini_service.generate_content", return_value="gemini reply")
def test_generate_uses_gemini_first(mock_gen):
    response = client.post("/api/v1/generate", json={"prompt": "Hi"})
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "gemini"
    assert data["response"] == "gemini reply"
    assert data["fallback_used"] is False


# ── Unified /generate (Gemini fails → Azure fallback) ───────
@patch("app.services.azure_openai_service.chat_completion", return_value="azure fallback reply")
@patch("app.services.gemini_service.generate_content", side_effect=Exception("429 RESOURCE_EXHAUSTED"))
def test_generate_falls_back_to_azure(mock_gen, mock_azure):
    response = client.post("/api/v1/generate", json={"prompt": "Hi"})
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "azure-openai"
    assert data["response"] == "azure fallback reply"
    assert data["fallback_used"] is True
    assert "RESOURCE_EXHAUSTED" in data["fallback_reason"]


# ── Unified /generate (both fail → 502) ─────────────────────
@patch("app.services.azure_openai_service.chat_completion", side_effect=Exception("Azure down"))
@patch("app.services.gemini_service.generate_content", side_effect=Exception("Gemini down"))
def test_generate_both_fail(mock_gen, mock_azure):
    response = client.post("/api/v1/generate", json={"prompt": "Hi"})
    assert response.status_code == 502
    assert "Both providers failed" in response.json()["detail"]


# ── Direct Gemini endpoint ──────────────────────────────────
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


# ── Direct Azure OpenAI endpoint ────────────────────────────
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
