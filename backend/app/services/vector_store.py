"""Persistent ChromaDB vector store for AI policy documents."""

from __future__ import annotations

import sys

# ---------------------------------------------------------------------------
# Monkey-patch pydantic v1 shim so chromadb can load on Python ≥ 3.14
# (pydantic v1's ModelField._set_default_and_type fails on PEP-728 style
#  annotations that Python 3.14 exposes).
# ---------------------------------------------------------------------------
if sys.version_info >= (3, 14):  # pragma: no cover
    try:
        from typing import Optional

        import pydantic.v1.fields as _pv1f

        _orig_set = _pv1f.ModelField._set_default_and_type

        def _patched_set(self: _pv1f.ModelField) -> None:  # type: ignore[override]
            try:
                _orig_set(self)
            except Exception:
                # Fall back: infer type from default when pydantic v1 can't
                # resolve the annotation on Python 3.14+.
                if self.default is None:
                    self.outer_type_ = Optional[str]
                    self.type_ = str
                    self.allow_none = True
                    self.required = False
                else:
                    self.outer_type_ = self.type_ = type(self.default)

        _pv1f.ModelField._set_default_and_type = _patched_set  # type: ignore[assignment]
    except Exception:
        pass

import chromadb


class PolicyVectorStore:
    """Thin wrapper around a persistent ChromaDB collection for AI policies."""

    COLLECTION_NAME = "ai_policies"

    def __init__(self, persist_directory: str = "./chroma_data") -> None:
        self._client = chromadb.PersistentClient(path=persist_directory)
        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
        )

    # ── write ────────────────────────────────────────────────
    def add_policy(self, id: str, text: str, embedding: list[float]) -> None:
        """Insert (or upsert) a single policy document with its embedding."""
        self._collection.upsert(
            ids=[id],
            documents=[text],
            embeddings=[embedding],
        )

    # ── read ─────────────────────────────────────────────────
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
    ) -> list[dict]:
        """Return the *top_k* most similar policies for the given embedding.

        Each result dict contains ``id``, ``document``, and ``distance``.
        """
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        hits: list[dict] = []
        for idx in range(len(results["ids"][0])):
            hits.append(
                {
                    "id": results["ids"][0][idx],
                    "document": results["documents"][0][idx],
                    "distance": results["distances"][0][idx],
                }
            )
        return hits

    # ── convenience ──────────────────────────────────────────
    async def get_relevant_policies(
        self,
        project_description: str,
        top_k: int = 3,
    ) -> list[str]:
        """Embed *project_description* and return the top-k policy texts.

        Uses :class:`AzureAIEngine` to generate the query embedding, then
        queries the ChromaDB collection for the nearest policy documents.
        """
        from app.services.ai_engine import AzureAIEngine

        engine = AzureAIEngine()
        query_embedding = await engine.get_embedding(project_description)
        hits = self.search(query_embedding=query_embedding, top_k=top_k)
        return [h["document"] for h in hits]
