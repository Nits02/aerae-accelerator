"""Tests for AzureAIEngine.get_embedding using AsyncMock."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.services.ai_engine import EMBEDDING_MODEL, AzureAIEngine

FAKE_EMBEDDING = [0.1, 0.2, 0.3, 0.4, 0.5]


def _mock_embedding_response(embedding: list[float] | None = None):
    """Build a minimal object that mirrors the OpenAI embeddings response."""
    vec = embedding or FAKE_EMBEDDING
    datum = SimpleNamespace(embedding=vec, index=0, object="embedding")
    return SimpleNamespace(data=[datum], model=EMBEDDING_MODEL, usage=SimpleNamespace(prompt_tokens=5, total_tokens=5))


# ── Tests ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_embedding_returns_list_of_floats():
    """get_embedding should return the embedding list from the API response."""
    engine = AzureAIEngine()
    engine._client.embeddings.create = AsyncMock(return_value=_mock_embedding_response())

    result = await engine.get_embedding("AI fairness policy")

    assert result == FAKE_EMBEDDING
    assert isinstance(result, list)
    assert all(isinstance(v, float) for v in result)


@pytest.mark.asyncio
async def test_get_embedding_calls_api_with_correct_args():
    """Ensure the embedding model and input text are forwarded to the SDK."""
    engine = AzureAIEngine()
    engine._client.embeddings.create = AsyncMock(return_value=_mock_embedding_response())

    await engine.get_embedding("test input")

    engine._client.embeddings.create.assert_awaited_once_with(
        model=EMBEDDING_MODEL,
        input="test input",
    )


@pytest.mark.asyncio
async def test_get_embedding_with_custom_vector():
    """The returned vector should match whatever the API sends back."""
    custom = [0.9, 0.8, 0.7]
    engine = AzureAIEngine()
    engine._client.embeddings.create = AsyncMock(return_value=_mock_embedding_response(custom))

    result = await engine.get_embedding("anything")

    assert result == custom
    assert len(result) == 3


@pytest.mark.asyncio
async def test_get_embedding_propagates_api_error():
    """An API error should propagate as-is to the caller."""
    engine = AzureAIEngine()
    engine._client.embeddings.create = AsyncMock(side_effect=RuntimeError("quota exceeded"))

    with pytest.raises(RuntimeError, match="quota exceeded"):
        await engine.get_embedding("boom")


@pytest.mark.asyncio
async def test_get_embedding_high_dimensional_vector():
    """Verify a realistic 1536-dim vector round-trips correctly."""
    big_vec = [float(i) / 1536 for i in range(1536)]
    engine = AzureAIEngine()
    engine._client.embeddings.create = AsyncMock(return_value=_mock_embedding_response(big_vec))

    result = await engine.get_embedding("long text")

    assert result == big_vec
    assert len(result) == 1536


@pytest.mark.asyncio
async def test_get_embedding_empty_string():
    """Even an empty string should go through and return the mocked vector."""
    engine = AzureAIEngine()
    engine._client.embeddings.create = AsyncMock(return_value=_mock_embedding_response())

    result = await engine.get_embedding("")

    engine._client.embeddings.create.assert_awaited_once_with(model=EMBEDDING_MODEL, input="")
    assert result == FAKE_EMBEDDING
