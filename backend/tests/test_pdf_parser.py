"""Tests for backend/app/services/pdf_parser.py"""

import json
from unittest.mock import MagicMock, patch

import pytest

# ── Hardcoded mock response ──────────────────────────────────
MOCK_EXTRACTED = {
    "project_purpose": "Automate ethical AI risk assessments for enterprise projects.",
    "data_types_used": ["personal data", "financial records", "health metrics"],
    "potential_risks": [
        "Bias in training data",
        "Lack of explainability",
        "Non-compliance with GDPR",
    ],
}

MOCK_JSON_STRING = json.dumps(MOCK_EXTRACTED)


# ── Helper: fake PDF bytes on disk ───────────────────────────
@pytest.fixture
def fake_pdf(tmp_path):
    """Create a minimal fake .pdf file so _read_pdf_bytes succeeds."""
    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake content")
    return str(pdf_file)


# ── 1. Azure OpenAI succeeds ────────────────────────────────
@patch("app.services.pdf_parser._extract_via_azure")
def test_parse_pdf_azure_success(mock_azure, fake_pdf):
    """When Azure OpenAI succeeds, parse_pdf returns its result without fallback."""
    mock_azure.return_value = MOCK_EXTRACTED.copy()

    from app.services.pdf_parser import parse_pdf

    result = parse_pdf(fake_pdf)

    mock_azure.assert_called_once()
    assert result["source"] == "azure-openai"
    assert result["fallback_used"] is False
    assert result["fallback_reason"] is None
    assert result["project_purpose"] == MOCK_EXTRACTED["project_purpose"]
    assert result["data_types_used"] == MOCK_EXTRACTED["data_types_used"]
    assert result["potential_risks"] == MOCK_EXTRACTED["potential_risks"]


# ── 2. Azure fails → Gemini fallback succeeds ───────────────
@patch("app.services.pdf_parser._extract_via_gemini")
@patch("app.services.pdf_parser._extract_via_azure", side_effect=Exception("Azure quota exceeded"))
def test_parse_pdf_falls_back_to_gemini(mock_azure, mock_gemini, fake_pdf):
    """When Azure OpenAI fails, parse_pdf falls back to Gemini."""
    mock_gemini.return_value = MOCK_EXTRACTED.copy()

    from app.services.pdf_parser import parse_pdf

    result = parse_pdf(fake_pdf)

    mock_azure.assert_called_once()
    mock_gemini.assert_called_once_with(fake_pdf)
    assert result["source"] == "gemini"
    assert result["fallback_used"] is True
    assert "Azure quota exceeded" in result["fallback_reason"]
    assert result["project_purpose"] == MOCK_EXTRACTED["project_purpose"]
    assert result["data_types_used"] == MOCK_EXTRACTED["data_types_used"]
    assert result["potential_risks"] == MOCK_EXTRACTED["potential_risks"]


# ── 3. Both providers fail ───────────────────────────────────
@patch("app.services.pdf_parser._extract_via_gemini", side_effect=Exception("Gemini 429"))
@patch("app.services.pdf_parser._extract_via_azure", side_effect=Exception("Azure 500"))
def test_parse_pdf_both_fail(mock_azure, mock_gemini, fake_pdf):
    """When both providers fail, parse_pdf raises RuntimeError."""
    from app.services.pdf_parser import parse_pdf

    with pytest.raises(RuntimeError, match="Both providers failed"):
        parse_pdf(fake_pdf)


# ── 4. File not found ───────────────────────────────────────
def test_parse_pdf_file_not_found():
    """parse_pdf raises FileNotFoundError for a missing file."""
    from app.services.pdf_parser import parse_pdf

    with pytest.raises(FileNotFoundError):
        parse_pdf("/nonexistent/path/doc.pdf")


# ── 5. Non-PDF file rejected ────────────────────────────────
def test_parse_pdf_rejects_non_pdf(tmp_path):
    """parse_pdf raises ValueError for non-.pdf extensions."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("hello")

    from app.services.pdf_parser import parse_pdf

    with pytest.raises(ValueError, match="Expected a .pdf file"):
        parse_pdf(str(txt_file))


# ── 6. _parse_json strips markdown fences ────────────────────
def test_parse_json_strips_fences():
    """_parse_json handles ```json ... ``` wrappers."""
    from app.services.pdf_parser import _parse_json

    wrapped = f"```json\n{MOCK_JSON_STRING}\n```"
    result = _parse_json(wrapped)
    assert result == MOCK_EXTRACTED


# ── 7. _parse_json rejects missing keys ─────────────────────
def test_parse_json_rejects_incomplete():
    """_parse_json raises ValueError when required keys are missing."""
    from app.services.pdf_parser import _parse_json

    incomplete = json.dumps({"project_purpose": "test"})
    with pytest.raises(ValueError, match="missing keys"):
        _parse_json(incomplete)


# ── 8. End-to-end with mocked Azure chat completion ─────────
@patch("app.services.pdf_parser._azure_client")
def test_extract_via_azure_end_to_end(mock_client, fake_pdf):
    """_extract_via_azure calls the chat completions API and parses JSON."""
    # Build a mock response chain: response.choices[0].message.content
    mock_message = MagicMock()
    mock_message.content = MOCK_JSON_STRING
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    from app.services.pdf_parser import _extract_via_azure, _read_pdf_bytes

    pdf_bytes = _read_pdf_bytes(fake_pdf)
    result = _extract_via_azure(pdf_bytes, "sample.pdf")

    mock_client.chat.completions.create.assert_called_once()
    assert result == MOCK_EXTRACTED


# ── 9. End-to-end with mocked Gemini upload + generate ──────
@patch("app.services.pdf_parser._gemini_client")
def test_extract_via_gemini_end_to_end(mock_client, fake_pdf):
    """_extract_via_gemini uploads file and calls generate_content."""
    mock_uploaded = MagicMock()
    mock_client.files.upload.return_value = mock_uploaded

    mock_response = MagicMock()
    mock_response.text = MOCK_JSON_STRING
    mock_client.models.generate_content.return_value = mock_response

    from app.services.pdf_parser import _extract_via_gemini

    result = _extract_via_gemini(fake_pdf)

    mock_client.files.upload.assert_called_once_with(file=fake_pdf)
    mock_client.models.generate_content.assert_called_once()
    assert result == MOCK_EXTRACTED
