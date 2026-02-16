"""Async Azure OpenAI engine – embeddings and chat via the openai SDK."""

from __future__ import annotations

import json

from openai import AsyncAzureOpenAI

from app.core.config import settings

EMBEDDING_MODEL = "text-embedding-3-small-1"
RISK_ANALYSIS_MODEL = "gpt-4o"

_RISK_SYSTEM_PROMPT = """\
You are an AI-risk analyst. You will receive:
1. A JSON object describing a software project (code metadata, optional PDF analysis, etc.).
2. A list of organisational AI-ethics / compliance policies.

Analyse the project against the policies and return a JSON object with a single
key "risks" whose value is an array of risk objects. Each risk object MUST have
exactly three fields:
  • "category"  – a short risk category label (e.g. "Data Privacy", "Bias", "Security").
  • "severity"  – one of "low", "medium", "high", or "critical".
  • "reason"    – a concise explanation of why this risk exists.

Return ONLY valid JSON. No markdown, no extra keys.
"""


class AzureAIEngine:
    """Async wrapper around Azure OpenAI for embeddings (and future chat)."""

    def __init__(self) -> None:
        self._client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        )

    async def get_embedding(self, text: str) -> list[float]:
        """Return the embedding vector for *text* using text-embedding-3-small."""
        response = await self._client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding

    async def analyze_risk(
        self,
        project_json: dict,
        policies: list[str],
    ) -> dict:
        """Analyse a project against policies and return structured risks.

        Returns a dict of the form::

            {
                "risks": [
                    {"category": "...", "severity": "...", "reason": "..."},
                    ...
                ]
            }
        """
        user_content = (
            "## Project context\n"
            f"```json\n{json.dumps(project_json, indent=2)}\n```\n\n"
            "## Applicable policies\n"
            + "\n".join(f"- {p}" for p in policies)
        )

        response = await self._client.chat.completions.create(
            model=RISK_ANALYSIS_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _RISK_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )

        return json.loads(response.choices[0].message.content)
