"""Google Gemini service – thin wrapper around the google-genai SDK."""

from google import genai

from app.core.config import settings

# Initialise the Gemini client with the API key from .env
_client = genai.Client(api_key=settings.GEMINI_API_KEY)

DEFAULT_MODEL = "gemini-2.0-flash"


def generate_content(prompt: str, model: str | None = None) -> str:
    """Send a prompt to Gemini and return the text response."""
    response = _client.models.generate_content(
        model=model or DEFAULT_MODEL,
        contents=prompt,
    )
    return response.text
