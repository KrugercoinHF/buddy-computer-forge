import hashlib
import subprocess
from pathlib import Path

import pytest

from repo_maintainer.skill_factory import (
    ALLOWED_CHECKS, build_proposal, validate_image, run_isolated_check,
)


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, text=True, capture_output=True
    ).stdout.strip()


def make_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-b", "base")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test")
    (root / "README.md").write_text("base\n")
    git(root, "add", ".")
    git(root, "commit", "-m", "base")
    git(root, "checkout", "-b", "agent/candidate")
    (root / "README.md").write_text("candidate\n")
    git(root, "add", "README.md")
    return root


def test_proposal_captures_patch_digest_and_quarantine_state(tmp_path):
    root = make_repo(tmp_path)
    proposal = build_proposal(root, "owner/repo", "base")
    assert proposal["state"] == "quarantined"
    assert proposal["requires_owner_approval"] is True
    assert proposal["release_allowed"] is False
    assert proposal["patch_sha256"] == hashlib.sha256(
        git(root, "diff", "--binary", "base").encode()
    ).hexdigest()
    assert proposal["changed_files"] == ["README.md"]


def test_untracked_files_are_not_silently_omitted(tmp_path):
    root = make_repo(tmp_path)
    (root / "new.py").write_text("print('candidate')\n")
    with pytest.raises(ValueError, match="untracked"):
        build_proposal(root, "owner/repo", "base")


def test_digest_pinned_image_required():
    with pytest.raises(ValueError, match="sha256"):
        validate_image("python:3.12")


def test_unknown_check_is_denied(tmp_path):
    root = make_repo(tmp_path)
    with pytest.raises(PermissionError):
        run_isolated_check(root, "runner@sha256:" + "a" * 64, "arbitrary-shell")


def test_check_commands_are_fixed():
    assert ALLOWED_CHECKS["pytest"] == ("python", "-m", "pytest", "-q")
