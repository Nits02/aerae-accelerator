"""Azure OpenAI service – thin wrapper around the openai SDK (Azure flavour)."""

from openai import AzureOpenAI

from app.core.config import settings

# Initialise the Azure OpenAI client with credentials from .env
_client = AzureOpenAI(
    api_key=settings.AZURE_OPENAI_API_KEY,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
)

DEFAULT_DEPLOYMENT = settings.AZURE_OPENAI_DEPLOYMENT_NAME


def chat_completion(prompt: str, deployment: str | None = None) -> str:
    """Send a prompt to Azure OpenAI and return the assistant's reply."""
    response = _client.chat.completions.create(
        model=deployment or DEFAULT_DEPLOYMENT,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content
