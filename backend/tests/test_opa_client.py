"""Tests for OPAGatekeeper – mocks the httpx POST to the local OPA server."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.opa_client import OPAGatekeeper


# ── helpers ──────────────────────────────────────────────────
def _mock_response(json_body: dict, status_code: int = 200) -> MagicMock:
    """Return a mock ``httpx.Response``."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_body
    resp.raise_for_status = MagicMock()
    return resp


def _patch_httpx(json_body: dict, status_code: int = 200):
    """Context-manager that patches ``httpx.AsyncClient`` to return *json_body*."""
    mock_resp = _mock_response(json_body, status_code)

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    return patch("app.services.opa_client.httpx.AsyncClient", return_value=mock_client), mock_client


# ── tests ────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_evaluate_payload_deny():
    """OPA returns allow=false with deny_reasons – parsed correctly."""
    body = {"result": {"allow": False, "deny_reasons": ["High risk"]}}
    patcher, mock_client = _patch_httpx(body)

    with patcher:
        gk = OPAGatekeeper()
        result = await gk.evaluate_payload({"secrets_count": 5})

    assert result == {"allow": False, "deny_reasons": ["High risk"]}
    mock_client.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_evaluate_payload_allow():
    """OPA returns allow=true with empty deny_reasons."""
    body = {"result": {"allow": True, "deny_reasons": []}}
    patcher, mock_client = _patch_httpx(body)

    with patcher:
        gk = OPAGatekeeper()
        result = await gk.evaluate_payload({"secrets_count": 0})

    assert result["allow"] is True
    assert result["deny_reasons"] == []


@pytest.mark.asyncio
async def test_evaluate_payload_sends_input_wrapper():
    """The payload is wrapped as ``{"input": payload}`` in the POST body."""
    body = {"result": {"allow": True, "deny_reasons": []}}
    patcher, mock_client = _patch_httpx(body)

    payload = {"secrets_count": 0, "risks": []}
    with patcher:
        gk = OPAGatekeeper()
        await gk.evaluate_payload(payload)

    _, kwargs = mock_client.post.call_args
    assert kwargs["json"] == {"input": payload}


@pytest.mark.asyncio
async def test_evaluate_payload_posts_to_correct_url():
    """POST goes to the default OPA ethical_gates URL."""
    body = {"result": {"allow": True, "deny_reasons": []}}
    patcher, mock_client = _patch_httpx(body)

    with patcher:
        gk = OPAGatekeeper()
        await gk.evaluate_payload({})

    args, _ = mock_client.post.call_args
    assert args[0] == OPAGatekeeper.DEFAULT_URL


@pytest.mark.asyncio
async def test_evaluate_payload_custom_url():
    """A custom OPA URL is respected."""
    body = {"result": {"allow": False, "deny_reasons": ["nope"]}}
    patcher, mock_client = _patch_httpx(body)
    custom = "http://opa.internal:9999/v1/data/custom_policy"

    with patcher:
        gk = OPAGatekeeper(url=custom)
        await gk.evaluate_payload({})

    args, _ = mock_client.post.call_args
    assert args[0] == custom


@pytest.mark.asyncio
async def test_evaluate_payload_missing_result_key():
    """When OPA response has no 'result' key, defaults to allow=False, empty deny_reasons."""
    patcher, _ = _patch_httpx({})

    with patcher:
        gk = OPAGatekeeper()
        result = await gk.evaluate_payload({})

    assert result == {"allow": False, "deny_reasons": []}


@pytest.mark.asyncio
async def test_evaluate_payload_multiple_deny_reasons():
    """Multiple deny_reasons are returned intact."""
    reasons = ["High risk", "Secrets detected", "Bias found"]
    body = {"result": {"allow": False, "deny_reasons": reasons}}
    patcher, _ = _patch_httpx(body)

    with patcher:
        gk = OPAGatekeeper()
        result = await gk.evaluate_payload({"secrets_count": 3})

    assert result["deny_reasons"] == reasons
    assert len(result["deny_reasons"]) == 3


@pytest.mark.asyncio
async def test_evaluate_payload_http_error():
    """An HTTP error from OPA propagates as an httpx.HTTPStatusError."""
    import httpx as _httpx

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.raise_for_status.side_effect = _httpx.HTTPStatusError(
        "Internal Server Error",
        request=MagicMock(),
        response=mock_resp,
    )

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.services.opa_client.httpx.AsyncClient", return_value=mock_client):
        gk = OPAGatekeeper()
        with pytest.raises(_httpx.HTTPStatusError):
            await gk.evaluate_payload({})


@pytest.mark.asyncio
async def test_evaluate_payload_critical_severity_deny():
    """OPA should deny when a critical-severity risk is present (e.g. EU AI Act prohibited practice)."""
    body = {
        "result": {
            "allow": False,
            "deny_reasons": [
                "Blocked: critical-severity risk found \u2014 Prohibited Practice: "
                "System uses subliminal manipulation violating EU AI Act"
            ],
        }
    }
    patcher, mock_client = _patch_httpx(body)

    with patcher:
        gk = OPAGatekeeper()
        result = await gk.evaluate_payload(
            {
                "secrets_count": 0,
                "risks": [
                    {
                        "category": "Prohibited Practice",
                        "severity": "critical",
                        "reason": "System uses subliminal manipulation violating EU AI Act",
                    }
                ],
            }
        )

    assert result["allow"] is False
    assert any("critical" in r.lower() for r in result["deny_reasons"])


@pytest.mark.asyncio
async def test_evaluate_payload_prohibited_use_case_deny():
    """OPA should deny when the project purpose is a prohibited use case (EU AI Act)."""
    body = {
        "result": {
            "allow": False,
            "deny_reasons": [
                "Blocked: Project purpose 'social_scoring' is a prohibited AI practice under the EU AI Act."
            ],
        }
    }
    patcher, mock_client = _patch_httpx(body)

    with patcher:
        gk = OPAGatekeeper()
        result = await gk.evaluate_payload(
            {
                "secrets_count": 0,
                "risks": [],
                "pdf_analysis": {
                    "project_purpose": "social_scoring",
                    "data_types_used": ["text"],
                    "human_in_the_loop": True,
                    "deployment_target": "private_cloud",
                },
                "code_metadata": {"deployment_target": "private_cloud"},
            }
        )

    assert result["allow"] is False
    assert any("prohibited" in r.lower() for r in result["deny_reasons"])


@pytest.mark.asyncio
async def test_evaluate_payload_missing_human_in_the_loop_deny():
    """OPA should deny high-severity risks when human_in_the_loop is not documented."""
    body = {
        "result": {
            "allow": False,
            "deny_reasons": [
                "Blocked: High-severity risks detected without a documented human-in-the-loop oversight mechanism."
            ],
        }
    }
    patcher, mock_client = _patch_httpx(body)

    with patcher:
        gk = OPAGatekeeper()
        result = await gk.evaluate_payload(
            {
                "secrets_count": 0,
                "risks": [
                    {
                        "category": "High-Risk System",
                        "severity": "high",
                        "reason": "Employment decision system without safeguards",
                    }
                ],
                "pdf_analysis": {
                    "project_purpose": "HR screening tool",
                    "data_types_used": ["pii"],
                    "human_in_the_loop": False,
                    "deployment_target": "private_cloud",
                },
                "code_metadata": {"deployment_target": "private_cloud"},
            }
        )

    assert result["allow"] is False
    assert any("human-in-the-loop" in r.lower() for r in result["deny_reasons"])


@pytest.mark.asyncio
async def test_evaluate_payload_biometric_public_cloud_deny():
    """OPA should deny when biometric data is deployed to public cloud."""
    body = {
        "result": {
            "allow": False,
            "deny_reasons": [
                "Blocked: Systems processing biometric data cannot be deployed to public-facing unvetted cloud environments."
            ],
        }
    }
    patcher, mock_client = _patch_httpx(body)

    with patcher:
        gk = OPAGatekeeper()
        result = await gk.evaluate_payload(
            {
                "secrets_count": 0,
                "risks": [],
                "pdf_analysis": {
                    "project_purpose": "Identity verification",
                    "data_types_used": ["biometric_data", "pii"],
                    "human_in_the_loop": True,
                    "deployment_target": "public_cloud",
                },
                "code_metadata": {"deployment_target": "public_cloud"},
            }
        )

    assert result["allow"] is False
    assert any("biometric" in r.lower() for r in result["deny_reasons"])
