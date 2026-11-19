from pathlib import Path
import subprocess
import pytest
from repo_maintainer.engine import RepositoryMaintainer
from repo_maintainer.policy import MaintainerPolicy

def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, text=True, capture_output=True).stdout.strip()

def make_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test")
    (root / "README.md").write_text("# demo\n")
    (root / "tests").mkdir()
    (root / "tests" / "test_demo.py").write_text("def test_demo(): assert True\n")
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / ".github" / "workflows" / "ci.yml").write_text("name: ci\n")
    git(root, "add", ".")
    git(root, "commit", "-m", "initial")
    return root

def test_inspection_is_read_only_and_clean(tmp_path):
    root = make_repo(tmp_path)
    before = git(root, "rev-parse", "HEAD")
    policy = MaintainerPolicy(allowed_repositories=frozenset({"owner/repo"}))
    report = RepositoryMaintainer(root, "owner/repo", policy).inspect()
    assert report["clean_worktree"] is True
    assert report["findings"] == []
    assert git(root, "rev-parse", "HEAD") == before
    assert git(root, "status", "--porcelain") == ""

def test_missing_quality_gates_are_reported(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test")
    (root / "README.md").write_text("hello")
    git(root, "add", ".")
    git(root, "commit", "-m", "initial")
    policy = MaintainerPolicy(allowed_repositories=frozenset({"owner/repo"}))
    codes = {f["code"] for f in RepositoryMaintainer(root, "owner/repo", policy).inspect()["findings"]}
    assert {"repo.tests.missing", "repo.ci.missing"} <= codes

def test_unknown_repository_is_denied(tmp_path):
    root = make_repo(tmp_path)
    with pytest.raises(PermissionError):
        RepositoryMaintainer(root, "other/repo", MaintainerPolicy(allowed_repositories=frozenset({"owner/repo"})))

def test_dirty_worktree_is_reported(tmp_path):
    root = make_repo(tmp_path)
    (root / "human.txt").write_text("keep me")
    policy = MaintainerPolicy(allowed_repositories=frozenset({"owner/repo"}))
    report = RepositoryMaintainer(root, "owner/repo", policy).inspect()
    assert report["clean_worktree"] is False
    assert any(f["code"] == "repo.worktree.dirty" for f in report["findings"])

def test_base_branch_allowlist_is_enforced(tmp_path):
    root = make_repo(tmp_path)
    maintainer = RepositoryMaintainer(root, "owner/repo", MaintainerPolicy(allowed_repositories=frozenset({"owner/repo"})))
    with pytest.raises(PermissionError):
        maintainer.propose("production")
