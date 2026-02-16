"""Tests for backend/app/services/git_scanner.py"""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from app.services.git_scanner import cleanup, clone_repo, clone_repo_context, list_files, _validate_url


# ── Safe public repo for integration tests ───────────────────
SAFE_REPO_URL = "https://github.com/octocat/Hello-World.git"


# ── 1. clone_repo returns an existing directory ──────────────
def test_clone_repo_creates_directory():
    """clone_repo should create a real directory on the filesystem."""
    dir_path, repo = clone_repo(SAFE_REPO_URL)
    try:
        assert os.path.isdir(dir_path), f"Expected directory to exist: {dir_path}"
        assert Path(dir_path, ".git").is_dir(), "Cloned repo should contain a .git folder"
        # Repo object should be usable
        assert repo.head.commit is not None
    finally:
        cleanup(dir_path)


# ── 2. cleanup removes the directory ────────────────────────
def test_cleanup_removes_directory():
    """After cleanup, the cloned directory should no longer exist."""
    dir_path, _ = clone_repo(SAFE_REPO_URL)
    assert os.path.isdir(dir_path)

    cleanup(dir_path)

    assert not os.path.exists(dir_path), f"Directory should be deleted: {dir_path}"


# ── 3. cleanup is safe to call twice ────────────────────────
def test_cleanup_idempotent():
    """Calling cleanup on an already-removed directory should not raise."""
    dir_path, _ = clone_repo(SAFE_REPO_URL)
    cleanup(dir_path)
    # Second call should be a no-op
    cleanup(dir_path)


# ── 4. clone_repo_context auto-cleans up ────────────────────
def test_clone_repo_context_auto_cleanup():
    """The context manager should clean up the directory on exit."""
    with clone_repo_context(SAFE_REPO_URL) as (dir_path, repo):
        assert os.path.isdir(dir_path)
        saved_path = dir_path

    assert not os.path.exists(saved_path), "Context manager should have cleaned up"


# ── 5. list_files returns repo contents ─────────────────────
def test_list_files_returns_files():
    """list_files should return at least one file from the cloned repo."""
    with clone_repo_context(SAFE_REPO_URL) as (dir_path, _):
        files = list_files(dir_path)
        assert len(files) > 0, "Hello-World repo should have at least one file"
        assert "README" in " ".join(files).upper(), "Hello-World should contain a README"


# ── 6. list_files with extension filter ─────────────────────
def test_list_files_with_extension_filter():
    """list_files with extensions filter should only return matching files."""
    with clone_repo_context(SAFE_REPO_URL) as (dir_path, _):
        md_files = list_files(dir_path, extensions={".md"})
        for f in md_files:
            assert f.endswith(".md"), f"Expected .md file, got: {f}"


# ── 7. Reject non-HTTPS URL ─────────────────────────────────
def test_rejects_ssh_url():
    """clone_repo should reject SSH URLs."""
    with pytest.raises(ValueError, match="Only HTTPS"):
        clone_repo("git@github.com:octocat/Hello-World.git")


# ── 8. Reject URL with embedded credentials ─────────────────
def test_rejects_embedded_credentials():
    """clone_repo should reject URLs with username:password."""
    with pytest.raises(ValueError, match="credentials"):
        clone_repo("https://user:pass@github.com/octocat/Hello-World.git")


# ── 9. Reject empty URL ─────────────────────────────────────
def test_rejects_empty_url():
    """clone_repo should reject empty strings."""
    with pytest.raises(ValueError, match="non-empty"):
        clone_repo("")


# ── 10. Invalid repo URL raises RuntimeError ────────────────
def test_clone_invalid_repo_raises():
    """clone_repo should raise RuntimeError for a non-existent repo."""
    with pytest.raises(RuntimeError, match="Failed to clone"):
        clone_repo("https://github.com/octocat/this-repo-does-not-exist-xyz-12345.git")
