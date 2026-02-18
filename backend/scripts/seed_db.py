#!/usr/bin/env python
"""Seed the PolicyVectorStore with AI-ethics and regulatory policies.

Seeds 9 policies covering internal ethics rules **and** global regulatory
frameworks (EU AI Act, NIST AI RMF, UNESCO).

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

# ── Internal AI-ethics rules ─────────────────────────────────
_ETHICS_POLICIES: list[dict[str, str]] = [
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

# ── Global regulatory & standards-based policies ─────────────
_REGULATORY_POLICIES: list[dict[str, str]] = [
    {
        "id": "eu-ai-act-001",
        "text": (
            "AI systems deploying subliminal, manipulative, or deceptive "
            "techniques to distort behavior and impair informed decision-making, "
            "causing significant harm, are strictly prohibited. Furthermore, "
            "biometric categorization systems inferring sensitive attributes "
            "(such as race, political opinions, or religious beliefs) and social "
            "scoring systems that categorize individuals based on social behavior "
            "leading to unjustified treatment are banned."
        ),
    },
    {
        "id": "eu-ai-act-002",
        "text": (
            "AI systems intended to be used as safety components in the management "
            "and operation of critical digital infrastructure, road traffic, or the "
            "supply of water, gas, heating, and electricity are classified as "
            "High-Risk. Similarly, AI systems used in employment, workers management, "
            "and access to self-employment are High-Risk and require strict risk "
            "mitigation and human oversight."
        ),
    },
    {
        "id": "nist-ai-rmf-001",
        "text": (
            "Accountability structures must be in place so that the appropriate "
            "teams and individuals are empowered, responsible, and trained for "
            "mapping, measuring, and managing AI risks. Organizations must identify "
            "and document the intended purpose, scope, and context of the AI system, "
            "including the data types used and the stakeholders impacted."
        ),
    },
    {
        "id": "unesco-001",
        "text": (
            "AI systems must incorporate human oversight and determination. AI "
            "should not replace essential human elements of teaching, mentoring, "
            "or high-stakes decision making without a human-in-the-loop validation "
            "process to prevent algorithmic bias."
        ),
    },
]

# ── Combined policy list ─────────────────────────────────────
POLICIES: list[dict[str, str]] = _ETHICS_POLICIES + _REGULATORY_POLICIES


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
    hits = store.search(query_embedding=query_embedding, top_k=min(len(POLICIES), 5))
    print(f"\nSanity search (top {len(hits)} for '{POLICIES[0]['id']}'):")
    for h in hits:
        print(f"  {h['id']}  dist={h['distance']:.4f}  {h['document'][:60]}…")

    print(f"\nDone – {len(POLICIES)} policies persisted to {settings.CHROMA_PERSIST_DIRECTORY}")


if __name__ == "__main__":
    asyncio.run(main())
