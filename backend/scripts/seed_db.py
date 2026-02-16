#!/usr/bin/env python
"""Seed the PolicyVectorStore with 5 AI-ethics rules.

Usage (from the backend/ directory):
    python -m scripts.seed_db
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure the backend package is importable when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.services.ai_engine import AzureAIEngine
from app.services.vector_store import PolicyVectorStore

# ── Hardcoded AI-ethics rules ────────────────────────────────
POLICIES: list[dict[str, str]] = [
    {
        "id": "ethics-001",
        "text": "No PII allowed without encryption at rest and in transit.",
    },
    {
        "id": "ethics-002",
        "text": (
            "AI systems must be regularly audited for bias across all "
            "protected demographic groups before deployment."
        ),
    },
    {
        "id": "ethics-003",
        "text": (
            "Training data should be representative and balanced to "
            "prevent discriminatory outcomes in model predictions."
        ),
    },
    {
        "id": "ethics-004",
        "text": (
            "All AI-driven decisions must be explainable and "
            "auditable by non-technical stakeholders."
        ),
    },
    {
        "id": "ethics-005",
        "text": (
            "Organisations must obtain informed consent before using "
            "personal data for AI model training."
        ),
    },
]


async def main() -> None:
    engine = AzureAIEngine()
    store = PolicyVectorStore(persist_directory=settings.CHROMA_PERSIST_DIRECTORY)

    print(f"Seeding {len(POLICIES)} AI-ethics rules into ChromaDB …\n")
    for policy in POLICIES:
        print(f"  → embedding '{policy['id']}' …", end=" ", flush=True)
        embedding = await engine.get_embedding(policy["text"])
        store.add_policy(id=policy["id"], text=policy["text"], embedding=embedding)
        print(f"done  (dim={len(embedding)})")

    # Quick sanity check – search with the first policy's own text
    query_embedding = await engine.get_embedding(POLICIES[0]["text"])
    hits = store.search(query_embedding=query_embedding, top_k=5)
    print(f"\nSanity search (top 5 for '{POLICIES[0]['id']}'):")
    for h in hits:
        print(f"  {h['id']}  dist={h['distance']:.4f}  {h['document'][:60]}…")

    print(f"\nDone – {len(POLICIES)} policies persisted to {settings.CHROMA_PERSIST_DIRECTORY}")


if __name__ == "__main__":
    asyncio.run(main())
