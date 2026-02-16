"""Git scanner service – securely clone public GitHub repos into temp directories.

Uses GitPython for cloning, tempfile / shutil for lifecycle management,
and the Gitleaks CLI for secret detection.
"""

import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

logger = logging.getLogger(__name__)


def clone_repo(repo_url: str) -> tuple[str, Repo]:
    """Clone a public GitHub repository into a temporary directory.

    Parameters
    ----------
    repo_url : str
        HTTPS URL of the public GitHub repository
        (e.g. ``https://github.com/owner/repo``).

    Returns
    -------
    tuple[str, Repo]
        A tuple of (temporary directory path, GitPython Repo object).
        The caller is responsible for calling :func:`cleanup` when done.

    Raises
    ------
    ValueError
        If the URL does not look like a valid GitHub HTTPS URL.
    RuntimeError
        If the clone operation fails.
    """
    _validate_url(repo_url)

    tmp_dir = tempfile.mkdtemp(prefix="aerae_git_")
    logger.info("Cloning %s into %s", repo_url, tmp_dir)

    try:
        repo = Repo.clone_from(
            repo_url,
            tmp_dir,
            depth=1,           # shallow clone – faster & lighter
            single_branch=True,
            no_checkout=False,
        )
        logger.info("Clone complete: %s (%s)", tmp_dir, repo.head.commit.hexsha[:8])
        return tmp_dir, repo
    except (GitCommandError, InvalidGitRepositoryError) as exc:
        # Clean up the temp dir if cloning failed
        cleanup(tmp_dir)
        raise RuntimeError(f"Failed to clone repository: {exc}") from exc


def clone_repo_context(repo_url: str):
    """Context-manager wrapper around :func:`clone_repo`.

    Automatically cleans up the temporary directory on exit.

    Usage::

        with clone_repo_context("https://github.com/owner/repo") as (dir_path, repo):
            # work with dir_path / repo
        # directory is removed here
    """
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        dir_path, repo = clone_repo(repo_url)
        try:
            yield dir_path, repo
        finally:
            cleanup(dir_path)

    return _ctx()


def cleanup(dir_path: str) -> None:
    """Remove a directory tree created by :func:`clone_repo`.

    Safe to call even if the directory has already been removed.

    Parameters
    ----------
    dir_path : str
        Absolute path to the directory to delete.
    """
    path = Path(dir_path)
    if not path.exists():
        logger.debug("Directory already removed: %s", dir_path)
        return

    try:
        shutil.rmtree(dir_path)
        logger.info("Cleaned up temporary directory: %s", dir_path)
    except OSError as exc:
        logger.error("Failed to clean up %s: %s", dir_path, exc)
        raise


def list_files(dir_path: str, extensions: set[str] | None = None) -> list[str]:
    """List files in a cloned repo, optionally filtered by extension.

    Parameters
    ----------
    dir_path : str
        Root directory of the cloned repository.
    extensions : set[str] | None
        If provided, only return files whose suffix is in this set
        (e.g. ``{".py", ".js", ".ts"}``). Pass ``None`` for all files.

    Returns
    -------
    list[str]
        Relative file paths (POSIX-style) from the repo root,
        excluding the ``.git`` directory.
    """
    root = Path(dir_path)
    results: list[str] = []
    for item in root.rglob("*"):
        if item.is_file() and ".git" not in item.parts:
            if extensions is None or item.suffix in extensions:
                results.append(str(item.relative_to(root)))
    return sorted(results)


# ── Gitleaks secret scanning ─────────────────────────────────
GITLEAKS_CMD = "gitleaks"


def scan_secrets(dir_path: str) -> dict:
    """Run Gitleaks against a directory and return a summary of findings.

    Parameters
    ----------
    dir_path : str
        Path to the cloned repository directory to scan.

    Returns
    -------
    dict
        {
            "secrets_found": int,
            "findings": list[dict],   # each finding from Gitleaks JSON
            "scan_successful": bool,
            "error": str | None,
        }

    Raises
    ------
    FileNotFoundError
        If the ``gitleaks`` CLI is not installed / not on PATH.
    """
    # Verify gitleaks is available
    if not shutil.which(GITLEAKS_CMD):
        raise FileNotFoundError(
            "Gitleaks CLI not found on PATH. "
            "Install it: https://github.com/gitleaks/gitleaks#installing"
        )

    if not Path(dir_path).is_dir():
        raise NotADirectoryError(f"Scan target is not a directory: {dir_path}")

    # Write results to a temp JSON file
    report_file = tempfile.NamedTemporaryFile(
        suffix=".json", prefix="gitleaks_report_", delete=False
    )
    report_path = report_file.name
    report_file.close()

    try:
        result = subprocess.run(
            [
                GITLEAKS_CMD,
                "detect",
                "--source", dir_path,
                "--report-format", "json",
                "--report-path", report_path,
                "--no-git",          # scan files directly (works with shallow clones)
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Gitleaks exit codes: 0 = no leaks, 1 = leaks found, >1 = error
        findings = _parse_gitleaks_report(report_path)

        if result.returncode > 1:
            logger.error("Gitleaks returned error code %d: %s", result.returncode, result.stderr)
            return {
                "secrets_found": 0,
                "findings": [],
                "scan_successful": False,
                "error": result.stderr.strip() or f"Gitleaks exit code {result.returncode}",
            }

        secret_count = len(findings)
        logger.info(
            "Gitleaks scan complete for %s: %d secret(s) found",
            dir_path, secret_count,
        )
        return {
            "secrets_found": secret_count,
            "findings": findings,
            "scan_successful": True,
            "error": None,
        }

    except subprocess.TimeoutExpired:
        logger.error("Gitleaks scan timed out for %s", dir_path)
        return {
            "secrets_found": 0,
            "findings": [],
            "scan_successful": False,
            "error": "Gitleaks scan timed out after 120 seconds",
        }
    finally:
        # Clean up the temporary report file
        Path(report_path).unlink(missing_ok=True)


def _parse_gitleaks_report(report_path: str) -> list[dict]:
    """Parse the Gitleaks JSON report file.

    Returns a list of finding dicts. Each finding contains keys like:
    ``Description``, ``File``, ``StartLine``, ``Secret``, ``RuleID``, etc.
    """
    path = Path(report_path)
    if not path.exists() or path.stat().st_size == 0:
        return []

    try:
        with open(path) as f:
            data = json.load(f)
        # Gitleaks outputs a JSON array of findings
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to parse Gitleaks report: %s", exc)
        return []


# ── Private helpers ──────────────────────────────────────────
def _validate_url(url: str) -> None:
    """Basic validation that the URL is an HTTPS GitHub URL."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("Repository URL must be a non-empty string.")
    if not url.startswith("https://"):
        raise ValueError(
            f"Only HTTPS URLs are supported for security. Got: {url}"
        )
    # Block embedded credentials (https://user:pass@...)
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.username or parsed.password:
        raise ValueError("Repository URL must not contain embedded credentials.")
