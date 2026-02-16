"""Tests for PolicyVectorStore using an in-memory ChromaDB client."""

from __future__ import annotations

import pytest

from app.services.vector_store import PolicyVectorStore


# ── Helpers ──────────────────────────────────────────────────

@pytest.fixture()
def store(tmp_path):
    """Return a PolicyVectorStore backed by a throwaway temp directory."""
    return PolicyVectorStore(persist_directory=str(tmp_path / "chroma_test"))


FAKE_EMBEDDING = [0.1, 0.2]


# ── Tests ────────────────────────────────────────────────────

def test_add_and_search_returns_dummy_policy(store: PolicyVectorStore):
    """Add a single dummy policy and verify it comes back from search."""
    store.add_policy(id="pol-1", text="All AI models must be explainable.", embedding=FAKE_EMBEDDING)

    hits = store.search(query_embedding=[0.1, 0.2], top_k=1)

    assert len(hits) == 1
    assert hits[0]["id"] == "pol-1"
    assert hits[0]["document"] == "All AI models must be explainable."
    assert "distance" in hits[0]


def test_search_with_similar_vector(store: PolicyVectorStore):
    """A slightly different query vector should still return the stored policy."""
    store.add_policy(id="pol-1", text="Data must be anonymised.", embedding=[0.1, 0.2])

    hits = store.search(query_embedding=[0.11, 0.21], top_k=1)

    assert len(hits) == 1
    assert hits[0]["id"] == "pol-1"


def test_search_top_k_limits_results(store: PolicyVectorStore):
    """Only top_k results should be returned even when more policies exist."""
    for i in range(5):
        store.add_policy(id=f"pol-{i}", text=f"Policy {i}", embedding=[float(i) * 0.1, float(i) * 0.2])

    hits = store.search(query_embedding=[0.0, 0.0], top_k=3)

    assert len(hits) == 3


def test_search_ordering_nearest_first(store: PolicyVectorStore):
    """The closest embedding should appear first in results."""
    store.add_policy(id="far", text="Far policy", embedding=[1.0, 1.0])
    store.add_policy(id="near", text="Near policy", embedding=[0.1, 0.1])

    hits = store.search(query_embedding=[0.1, 0.1], top_k=2)

    assert hits[0]["id"] == "near"
    assert hits[0]["distance"] <= hits[1]["distance"]


def test_upsert_overwrites_existing_policy(store: PolicyVectorStore):
    """Adding a policy with the same id should update the document text."""
    store.add_policy(id="pol-1", text="Original text.", embedding=FAKE_EMBEDDING)
    store.add_policy(id="pol-1", text="Updated text.", embedding=FAKE_EMBEDDING)

    hits = store.search(query_embedding=FAKE_EMBEDDING, top_k=1)

    assert hits[0]["document"] == "Updated text."


def test_search_empty_collection_returns_nothing(store: PolicyVectorStore):
    """Searching an empty collection should return an empty list."""
    hits = store.search(query_embedding=FAKE_EMBEDDING, top_k=3)

    assert hits == []


def test_collection_name(store: PolicyVectorStore):
    """The collection should be named 'ai_policies'."""
    assert store.COLLECTION_NAME == "ai_policies"
    assert store._collection.name == "ai_policies"


def test_multiple_policies_all_returned(store: PolicyVectorStore):
    """When fewer policies exist than top_k, all should be returned."""
    store.add_policy(id="a", text="Policy A", embedding=[0.1, 0.2])
    store.add_policy(id="b", text="Policy B", embedding=[0.3, 0.4])

    hits = store.search(query_embedding=[0.2, 0.3], top_k=10)

    assert len(hits) == 2
    returned_ids = {h["id"] for h in hits}
    assert returned_ids == {"a", "b"}
