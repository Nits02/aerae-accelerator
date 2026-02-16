"""OPA Gatekeeper – async client for the Open Policy Agent REST API."""

from __future__ import annotations

import httpx


class OPAGatekeeper:
    """Evaluate payloads against the *ethical_gates* Rego policy via a local OPA server."""

    DEFAULT_URL = "http://localhost:8181/v1/data/ethical_gates"

    def __init__(self, url: str = DEFAULT_URL) -> None:
        self.url = url

    async def evaluate_payload(self, payload: dict) -> dict:
        """POST *payload* as OPA input and return ``{"allow": bool, "deny_reasons": list}``."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.url,
                json={"input": payload},
                timeout=10.0,
            )
            response.raise_for_status()

        result = response.json().get("result", {})
        return {
            "allow": result.get("allow", False),
            "deny_reasons": result.get("deny_reasons", []),
        }
