"""Tests for git_scanner.scan_secrets – mocked subprocess & Gitleaks output."""

import json
import os
import tempfile
from subprocess import CompletedProcess
from unittest.mock import patch, MagicMock

import pytest

from app.services.git_scanner import scan_secrets, _parse_gitleaks_report


# ── Fake Gitleaks findings (2 leaked secrets) ────────────────
FAKE_FINDINGS = [
    {
        "Description": "AWS Access Key",
        "StartLine": 12,
        "EndLine": 12,
        "StartColumn": 1,
        "EndColumn": 40,
        "Match": "AKIAIOSFODNN7EXAMPLE",
        "Secret": "AKIAIOSFODNN7EXAMPLE",
        "File": "config/settings.py",
        "SymlinkFile": "",
        "Commit": "",
        "Entropy": 3.52,
        "Author": "",
        "Email": "",
        "Date": "",
        "Message": "",
        "Tags": [],
        "RuleID": "aws-access-key-id",
        "Fingerprint": "config/settings.py:aws-access-key-id:12",
    },
    {
        "Description": "Generic API Key",
        "StartLine": 25,
        "EndLine": 25,
        "StartColumn": 1,
        "EndColumn": 55,
        "Match": "api_key = 'sk-live-abc123def456ghi789jkl012mno345'",
        "Secret": "sk-live-abc123def456ghi789jkl012mno345",
        "File": "src/main.py",
        "SymlinkFile": "",
        "Commit": "",
        "Entropy": 4.12,
        "Author": "",
        "Email": "",
        "Date": "",
        "Message": "",
        "Tags": [],
        "RuleID": "generic-api-key",
        "Fingerprint": "src/main.py:generic-api-key:25",
    },
]


@pytest.fixture
def scan_dir(tmp_path):
    """Create a temporary directory to act as the scan target."""
    target = tmp_path / "repo"
    target.mkdir()
    (target / "README.md").write_text("# Hello")
    return str(target)


# ── 1. scan_secrets returns 2 when Gitleaks finds 2 leaks ───
@patch("app.services.git_scanner.shutil.which", return_value="/usr/local/bin/gitleaks")
@patch("app.services.git_scanner.subprocess.run")
def test_scan_secrets_two_leaks(mock_run, mock_which, scan_dir):
    """scan_secrets should parse the report and return secrets_found=2."""

    def _fake_run(cmd, **kwargs):
        # Write the fake findings into the report file that scan_secrets created
        report_path = cmd[cmd.index("--report-path") + 1]
        with open(report_path, "w") as f:
            json.dump(FAKE_FINDINGS, f)
        return CompletedProcess(args=cmd, returncode=1, stdout="", stderr="")

    mock_run.side_effect = _fake_run

    result = scan_secrets(scan_dir)

    assert result["scan_successful"] is True
    assert result["secrets_found"] == 2
    assert result["error"] is None
    assert len(result["findings"]) == 2
    assert result["findings"][0]["RuleID"] == "aws-access-key-id"
    assert result["findings"][1]["RuleID"] == "generic-api-key"


# ── 2. scan_secrets returns 0 when no leaks ─────────────────
@patch("app.services.git_scanner.shutil.which", return_value="/usr/local/bin/gitleaks")
@patch("app.services.git_scanner.subprocess.run")
def test_scan_secrets_no_leaks(mock_run, mock_which, scan_dir):
    """scan_secrets should return 0 secrets when Gitleaks finds nothing."""

    def _fake_run(cmd, **kwargs):
        report_path = cmd[cmd.index("--report-path") + 1]
        with open(report_path, "w") as f:
            json.dump([], f)
        return CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    mock_run.side_effect = _fake_run

    result = scan_secrets(scan_dir)

    assert result["scan_successful"] is True
    assert result["secrets_found"] == 0
    assert result["findings"] == []


# ── 3. scan_secrets handles Gitleaks error (exit code > 1) ──
@patch("app.services.git_scanner.shutil.which", return_value="/usr/local/bin/gitleaks")
@patch("app.services.git_scanner.subprocess.run")
def test_scan_secrets_gitleaks_error(mock_run, mock_which, scan_dir):
    """scan_secrets should report failure when Gitleaks exits with code > 1."""

    def _fake_run(cmd, **kwargs):
        return CompletedProcess(
            args=cmd, returncode=2, stdout="", stderr="fatal: config error"
        )

    mock_run.side_effect = _fake_run

    result = scan_secrets(scan_dir)

    assert result["scan_successful"] is False
    assert result["secrets_found"] == 0
    assert "config error" in result["error"]


# ── 4. scan_secrets handles timeout ─────────────────────────
@patch("app.services.git_scanner.shutil.which", return_value="/usr/local/bin/gitleaks")
@patch("app.services.git_scanner.subprocess.run")
def test_scan_secrets_timeout(mock_run, mock_which, scan_dir):
    """scan_secrets should handle subprocess timeout gracefully."""
    import subprocess

    mock_run.side_effect = subprocess.TimeoutExpired(cmd="gitleaks", timeout=120)

    result = scan_secrets(scan_dir)

    assert result["scan_successful"] is False
    assert result["secrets_found"] == 0
    assert "timed out" in result["error"]


# ── 5. scan_secrets raises if gitleaks not installed ─────────
@patch("app.services.git_scanner.shutil.which", return_value=None)
def test_scan_secrets_missing_gitleaks(mock_which, scan_dir):
    """scan_secrets should raise FileNotFoundError when gitleaks is not on PATH."""
    with pytest.raises(FileNotFoundError, match="Gitleaks CLI not found"):
        scan_secrets(scan_dir)


# ── 6. scan_secrets raises for invalid directory ────────────
@patch("app.services.git_scanner.shutil.which", return_value="/usr/local/bin/gitleaks")
def test_scan_secrets_invalid_directory(mock_which):
    """scan_secrets should raise NotADirectoryError for non-existent path."""
    with pytest.raises(NotADirectoryError):
        scan_secrets("/nonexistent/path/repo")


# ── 7. _parse_gitleaks_report with valid JSON ───────────────
def test_parse_report_valid(tmp_path):
    """_parse_gitleaks_report should return the list of findings."""
    report = tmp_path / "report.json"
    report.write_text(json.dumps(FAKE_FINDINGS))

    findings = _parse_gitleaks_report(str(report))

    assert len(findings) == 2
    assert findings[0]["Secret"] == "AKIAIOSFODNN7EXAMPLE"
    assert findings[1]["File"] == "src/main.py"


# ── 8. _parse_gitleaks_report with empty file ───────────────
def test_parse_report_empty(tmp_path):
    """_parse_gitleaks_report should return [] for an empty report file."""
    report = tmp_path / "report.json"
    report.write_text("")

    assert _parse_gitleaks_report(str(report)) == []


# ── 9. _parse_gitleaks_report with missing file ─────────────
def test_parse_report_missing():
    """_parse_gitleaks_report should return [] for a non-existent file."""
    assert _parse_gitleaks_report("/no/such/report.json") == []


# ── 10. _parse_gitleaks_report with malformed JSON ──────────
def test_parse_report_malformed(tmp_path):
    """_parse_gitleaks_report should return [] for invalid JSON."""
    report = tmp_path / "report.json"
    report.write_text("{not valid json!!!")

    assert _parse_gitleaks_report(str(report)) == []
