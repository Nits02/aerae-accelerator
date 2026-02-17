"""PDF parser service – extracts structured project metadata from PDF files.

Extracts text from the PDF using pypdf, then sends the text to Azure OpenAI
(chat completion) for structured analysis. Falls back to Google Gemini on failure.
Returns a strict JSON dict with project purpose, data types, and risks.
"""

import json
import logging
from pathlib import Path

from google import genai
from openai import AzureOpenAI
from pypdf import PdfReader

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Clients ──────────────────────────────────────────────────
_azure_client = AzureOpenAI(
    api_key=settings.AZURE_OPENAI_API_KEY,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
)

_gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

# ── Constants ────────────────────────────────────────────────
AZURE_DEPLOYMENT = settings.AZURE_OPENAI_DEPLOYMENT_NAME
GEMINI_MODEL = "gemini-2.0-flash-lite"

EXTRACTION_PROMPT = """\
You are a document analysis assistant. Analyse the following document text
and extract the information into **strict JSON** (no markdown fences, no extra keys):

{
  "project_purpose": "<concise summary of the project's purpose>",
  "data_types_used": ["<data type 1>", "<data type 2>", "..."],
  "potential_risks": ["<risk 1>", "<risk 2>", "..."]
}

Rules:
- "project_purpose" must be a single string (1-3 sentences).
- "data_types_used" must list every distinct data / data-type category mentioned.
- "potential_risks" must list concrete risks or concerns found in the document.
- If a section has no relevant info, use an empty list [] or "Not specified".
- Output ONLY the JSON object, nothing else.
"""


def _read_pdf_bytes(file_path: str) -> bytes:
    """Read raw bytes from a PDF file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")
    if not path.suffix.lower() == ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {path.suffix}")
    return path.read_bytes()


def _extract_text(file_path: str) -> str:
    """Extract plain text from a PDF using pypdf."""
    reader = PdfReader(file_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages).strip()
    if not text:
        raise ValueError("PDF contains no extractable text.")
    # Truncate to ~12 000 chars to stay within token limits
    return text[:12_000]


# ── Azure OpenAI approach ────────────────────────────────────
def _extract_via_azure(pdf_text: str) -> dict:
    """Send extracted PDF text to Azure OpenAI and parse the JSON response."""
    response = _azure_client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful document analysis assistant.",
            },
            {
                "role": "user",
                "content": f"{EXTRACTION_PROMPT}\n\n--- DOCUMENT TEXT ---\n{pdf_text}",
            },
        ],
    )
    raw = response.choices[0].message.content.strip()
    return _parse_json(raw)


# ── Gemini approach ──────────────────────────────────────────
def _extract_via_gemini(pdf_text: str) -> dict:
    """Send extracted PDF text to Gemini and parse the JSON response."""
    response = _gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[f"{EXTRACTION_PROMPT}\n\n--- DOCUMENT TEXT ---\n{pdf_text}"],
    )
    raw = response.text.strip()
    return _parse_json(raw)


# ── JSON parser helper ───────────────────────────────────────
def _parse_json(raw_text: str) -> dict:
    """Attempt to parse JSON from model output, stripping markdown fences if present."""
    text = raw_text.strip()
    # Strip ```json ... ``` wrappers
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    parsed = json.loads(text)

    # Validate expected keys
    expected = {"project_purpose", "data_types_used", "potential_risks"}
    if not expected.issubset(parsed.keys()):
        missing = expected - parsed.keys()
        raise ValueError(f"Model response missing keys: {missing}")

    return parsed


# ── Public API ───────────────────────────────────────────────
def parse_pdf(file_path: str) -> dict:
    """Extract project metadata from a PDF.

    Tries Azure OpenAI first; falls back to Google Gemini on any failure.

    Returns
    -------
    dict
        {
            "project_purpose": str,
            "data_types_used": list[str],
            "potential_risks": list[str],
            "source": "azure-openai" | "gemini",
            "fallback_used": bool,
            "fallback_reason": str | None,
        }
    """
    pdf_bytes = _read_pdf_bytes(file_path)
    pdf_text = _extract_text(file_path)
    filename = Path(file_path).name

    # --- Try Azure OpenAI first ---
    try:
        result = _extract_via_azure(pdf_text)
        result["source"] = "azure-openai"
        result["fallback_used"] = False
        result["fallback_reason"] = None
        logger.info("PDF parsed successfully via Azure OpenAI")
        return result
    except Exception as azure_exc:
        azure_error = str(azure_exc)
        logger.warning("Azure OpenAI PDF parsing failed (%s), falling back to Gemini", azure_error)

    # --- Fallback to Gemini ---
    try:
        result = _extract_via_gemini(pdf_text)
        result["source"] = "gemini"
        result["fallback_used"] = True
        result["fallback_reason"] = f"Azure OpenAI unavailable: {azure_error}"
        logger.info("PDF parsed successfully via Gemini (fallback)")
        return result
    except Exception as gemini_exc:
        raise RuntimeError(
            f"Both providers failed to parse PDF. "
            f"Azure OpenAI: {azure_error} | Gemini: {gemini_exc}"
        )
