"""Tests for AzureAIEngine.analyze_risk using AsyncMock."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.ai_engine import AzureAIEngine, RISK_ANALYSIS_MODEL

# ── Hardcoded mock response ──────────────────────────────────
MOCK_RISK_JSON = json.dumps(
    {
        "risks": [
            {
                "category": "Data Privacy",
                "severity": "high",
                "reason": "PII is collected without encryption.",
            }
        ]
    }
)


def _mock_chat_response(content: str = MOCK_RISK_JSON):
    """Build a minimal object mirroring the OpenAI chat completion response."""
    message = SimpleNamespace(content=content, role="assistant")
    choice = SimpleNamespace(message=message, index=0, finish_reason="stop")
    return SimpleNamespace(choices=[choice], model=RISK_ANALYSIS_MODEL)


SAMPLE_PROJECT = {
    "project_name": "Test Project",
    "source_url": "https://github.com/example/test",
    "code_metadata": {"files_count": 5, "secrets_found": 0},
}

SAMPLE_POLICIES = [
    "No PII allowed without encryption at rest and in transit.",
    "AI systems must be regularly audited for bias.",
]


# ── Tests ────────────────────────────────────────────────────

async def test_analyze_risk_returns_high_severity_risk():
    """analyze_risk should parse the mocked JSON and contain a 'high' severity risk."""
    engine = AzureAIEngine()
    engine._client.chat.completions.create = AsyncMock(return_value=_mock_chat_response())

    result = await engine.analyze_risk(SAMPLE_PROJECT, SAMPLE_POLICIES)

    assert "risks" in result
    assert len(result["risks"]) == 1

    risk = result["risks"][0]
    assert risk["severity"] == "high"
    assert risk["category"] == "Data Privacy"
    assert risk["reason"] == "PII is collected without encryption."


async def test_analyze_risk_calls_gpt4o_with_json_format():
    """Verify the correct model and response_format are forwarded to the SDK."""
    engine = AzureAIEngine()
    engine._client.chat.completions.create = AsyncMock(return_value=_mock_chat_response())

    await engine.analyze_risk(SAMPLE_PROJECT, SAMPLE_POLICIES)

    call_kwargs = engine._client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == RISK_ANALYSIS_MODEL
    assert call_kwargs["response_format"] == {"type": "json_object"}


async def test_analyze_risk_prompt_contains_project_and_policies():
    """The user message should include both the project JSON and the policies."""
    engine = AzureAIEngine()
    engine._client.chat.completions.create = AsyncMock(return_value=_mock_chat_response())

    await engine.analyze_risk(SAMPLE_PROJECT, SAMPLE_POLICIES)

    messages = engine._client.chat.completions.create.call_args.kwargs["messages"]
    user_msg = messages[1]["content"]
    assert "Test Project" in user_msg
    assert "No PII allowed" in user_msg
    assert "audited for bias" in user_msg


async def test_analyze_risk_multiple_risks():
    """Should handle a response with several risks."""
    multi = json.dumps(
        {
            "risks": [
                {"category": "Data Privacy", "severity": "high", "reason": "reason1"},
                {"category": "Bias", "severity": "medium", "reason": "reason2"},
            ]
        }
    )
    engine = AzureAIEngine()
    engine._client.chat.completions.create = AsyncMock(return_value=_mock_chat_response(multi))

    result = await engine.analyze_risk(SAMPLE_PROJECT, SAMPLE_POLICIES)

    assert len(result["risks"]) == 2
    severities = {r["severity"] for r in result["risks"]}
    assert "high" in severities
    assert "medium" in severities


async def test_analyze_risk_propagates_api_error():
    """An API error should propagate to the caller."""
    engine = AzureAIEngine()
    engine._client.chat.completions.create = AsyncMock(side_effect=RuntimeError("service down"))

    with pytest.raises(RuntimeError, match="service down"):
        await engine.analyze_risk(SAMPLE_PROJECT, SAMPLE_POLICIES)
