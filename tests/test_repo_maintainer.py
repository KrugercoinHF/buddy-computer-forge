from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess

import pytest

from repo_maintainer.cli import load_trusted_policy, normalize_github_remote, verify_checkout_origin
from repo_maintainer.engine import RepositoryMaintainer
from repo_maintainer.models import VerifiedApproval
from repo_maintainer.policy import MaintainerPolicy


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, text=True, capture_output=True
    ).stdout.strip()


def make_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test")
    (root / "README.md").write_text("# demo\\n")
    (root / "tests").mkdir()
    (root / "tests" / "test_demo.py").write_text("def test_demo(): assert True\\n")
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / ".github" / "workflows" / "ci.yml").write_text("name: ci\\n")
    git(root, "add", ".")
    git(root, "commit", "-m", "initial")
    return root


def make_maintainer(root: Path) -> RepositoryMaintainer:
    policy = MaintainerPolicy(allowed_repositories=frozenset({"owner/repo"}))
    return RepositoryMaintainer(root, "owner/repo", policy)


def test_inspection_is_read_only_and_clean(tmp_path):
    root = make_repo(tmp_path)
    before = git(root, "rev-parse", "HEAD")
    report = make_maintainer(root).inspect()
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
    codes = {f["code"] for f in make_maintainer(root).inspect()["findings"]}
    assert {"repo.tests.missing", "repo.ci.missing"} <= codes


def test_unknown_repository_is_denied(tmp_path):
    root = make_repo(tmp_path)
    with pytest.raises(PermissionError):
        RepositoryMaintainer(
            root, "other/repo",
            MaintainerPolicy(allowed_repositories=frozenset({"owner/repo"})),
        )


def test_dirty_worktree_is_reported(tmp_path):
    root = make_repo(tmp_path)
    (root / "human.txt").write_text("keep me")
    report = make_maintainer(root).inspect()
    assert report["clean_worktree"] is False
    assert any(f["code"] == "repo.worktree.dirty" for f in report["findings"])


def test_base_branch_allowlist_is_enforced(tmp_path):
    maintainer = make_maintainer(make_repo(tmp_path))
    with pytest.raises(PermissionError):
        maintainer.propose("production")


def test_approval_cannot_be_created_from_a_claimed_name(tmp_path):
    maintainer = make_maintainer(make_repo(tmp_path))
    proposal = maintainer.propose("main")
    with pytest.raises(PermissionError, match="trusted approval gateway"):
        maintainer.record_approval(proposal, "owner", ("file_writes",))


class FakeApprovalGateway:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def verify_approval(self, approval_token, proposal_digest, approved_scope):
        self.calls.append((approval_token, proposal_digest, approved_scope))
        return self.result


def test_approval_requires_gateway_verified_identity_and_exact_scope(tmp_path):
    root = make_repo(tmp_path)
    policy = MaintainerPolicy(allowed_repositories=frozenset({"owner/repo"}))
    proposal = RepositoryMaintainer(root, "owner/repo", policy).propose("main")
    digest = RepositoryMaintainer.proposal_digest(proposal)
    scope = ("file_writes",)
    evidence = VerifiedApproval(
        subject="owner",
        proposal_digest=digest,
        approved_scope=scope,
        token_id="one-time-approval-001",
        expires_at=(datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        verifier="buddy-approval-gateway",
    )
    gateway = FakeApprovalGateway(evidence)
    maintainer = RepositoryMaintainer(root, "owner/repo", policy, gateway)
    record = maintainer.record_approval(proposal, "signed-token", scope)
    assert record["approver"] == "owner"
    assert record["proposal_digest"] == digest
    assert record["approved_scope"] == ["file_writes"]
    assert gateway.calls == [("signed-token", digest, scope)]


def test_approval_gateway_result_for_another_proposal_is_rejected(tmp_path):
    root = make_repo(tmp_path)
    policy = MaintainerPolicy(allowed_repositories=frozenset({"owner/repo"}))
    proposal = RepositoryMaintainer(root, "owner/repo", policy).propose("main")
    wrong = VerifiedApproval(
        subject="owner", proposal_digest="wrong-digest", approved_scope=("file_writes",),
        token_id="approval-002",
        expires_at=(datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        verifier="buddy-approval-gateway",
    )
    maintainer = RepositoryMaintainer(root, "owner/repo", policy, FakeApprovalGateway(wrong))
    with pytest.raises(PermissionError, match="does not match"):
        maintainer.record_approval(proposal, "signed-token", ("file_writes",))


def test_expired_gateway_approval_is_rejected(tmp_path):
    root = make_repo(tmp_path)
    policy = MaintainerPolicy(allowed_repositories=frozenset({"owner/repo"}))
    proposal = RepositoryMaintainer(root, "owner/repo", policy).propose("main")
    evidence = VerifiedApproval(
        subject="owner", proposal_digest=RepositoryMaintainer.proposal_digest(proposal),
        approved_scope=("file_writes",), token_id="expired",
        expires_at=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
        verifier="buddy-approval-gateway",
    )
    maintainer = RepositoryMaintainer(root, "owner/repo", policy, FakeApprovalGateway(evidence))
    with pytest.raises(PermissionError, match="expired"):
        maintainer.record_approval(proposal, "signed-token", ("file_writes",))


def test_github_remote_normalization():
    assert normalize_github_remote("https://github.com/owner/repo.git") == "https://github.com/owner/repo.git"
    assert normalize_github_remote("git@github.com:owner/repo.git") == "https://github.com/owner/repo.git"
    assert normalize_github_remote("ssh://git@github.com/owner/repo") == "https://github.com/owner/repo.git"
    with pytest.raises(PermissionError):
        normalize_github_remote("https://evil.example/owner/repo.git")


def test_checkout_origin_must_match_trusted_origin(tmp_path):
    root = make_repo(tmp_path)
    git(root, "remote", "add", "origin", "git@github.com:owner/repo.git")
    verify_checkout_origin(root, "https://github.com/owner/repo.git")
    with pytest.raises(PermissionError, match="origin mismatch"):
        verify_checkout_origin(root, "https://github.com/other/repo.git")


def test_policy_is_external_and_allowlisted(tmp_path):
    root = make_repo(tmp_path)
    policy_file = tmp_path / "trusted-policy.json"
    policy_file.write_text(json.dumps({
        "repositories": {
            "owner/repo": {
                "origin": "https://github.com/owner/repo.git",
                "allowed_base_branches": ["main"],
            }
        }
    }))
    policy_file.chmod(0o600)
    policy, origin = load_trusted_policy(policy_file, root, "owner/repo")
    assert origin == "https://github.com/owner/repo.git"
    assert "owner/repo" in policy.allowed_repositories
    with pytest.raises(PermissionError, match="not in trusted policy"):
        load_trusted_policy(policy_file, root, "attacker/repo")
    with pytest.raises(PermissionError, match="outside"):
        load_trusted_policy(root / "README.md", root, "owner/repo")
