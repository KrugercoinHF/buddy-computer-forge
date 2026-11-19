import hashlib
import json
import subprocess
from pathlib import Path
from .models import Finding, WorkProposal
from .policy import MaintainerPolicy

class RepositoryMaintainer:
    """Read-only local Git inspection and approval-bound proposal generation."""
    def __init__(self, root: str | Path, repository: str, policy: MaintainerPolicy):
        self.root = Path(root).resolve()
        self.repository = repository
        self.policy = policy
        if not self.root.is_dir():
            raise ValueError("repository root must be an existing directory")
        self.policy.validate_repository(repository)
    def _git(self, *args: str) -> str:
        result = subprocess.run(["git", *args], cwd=self.root, text=True, capture_output=True, check=True)
        return result.stdout.strip()
    def inspect(self) -> dict:
        branch = self._git("branch", "--show-current")
        head = self._git("rev-parse", "HEAD")
        status = self._git("status", "--porcelain=v1")
        tracked = self._git("ls-files").splitlines()
        paths = set(tracked)
        findings: list[Finding] = []
        if "README.md" not in paths:
            findings.append(Finding("repo.readme.missing", "medium", "README is missing", "Add setup, test and contribution guidance.", "README.md"))
        if not any(p.startswith(("tests/", "test/")) or p.startswith("tests\\") for p in paths):
            findings.append(Finding("repo.tests.missing", "high", "No tracked test directory found", "Add automated tests before enabling autonomous code changes."))
        if not any(p.startswith(".github/workflows/") for p in paths):
            findings.append(Finding("repo.ci.missing", "high", "No GitHub Actions workflow found", "Add CI for tests, lint and security checks."))
        if status:
            findings.append(Finding("repo.worktree.dirty", "high", "Working tree is not clean", "Do not overwrite or mix uncommitted human changes."))
        return {"repository": self.repository, "root": str(self.root), "branch": branch, "head": head,
                "clean_worktree": not bool(status), "tracked_files": len(tracked),
                "findings": [f.__dict__ for f in findings]}
    def propose(self, base_ref: str = "main") -> WorkProposal:
        self.policy.validate_base(base_ref)
        report = self.inspect()
        findings = tuple(Finding(**item) for item in report["findings"])
        raw = self.repository + report["head"] + json.dumps(report["findings"], sort_keys=True)
        digest = hashlib.sha256(raw.encode()).hexdigest()[:12]
        return WorkProposal(f"repo-maint-{digest}", self.repository, base_ref, f"agent/repo-maint-{digest}",
            f"Repository inspection found {len(findings)} maintenance item(s); proposal only.", findings,
            ("python -m pytest", "ruff check .", "bandit -r ."))
    def record_approval(self, proposal: WorkProposal, approver: str, approved_scope: tuple[str, ...]) -> dict:
        if not approver.strip() or approver.lower() in {"agent", "system", "maintainer-bot"}:
            raise PermissionError("approval must come from an identified human owner or delegate")
        payload = {"proposal": proposal.to_dict(), "approver": approver, "approved_scope": list(approved_scope), "decision": "approved"}
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        payload["approval_digest"] = hashlib.sha256(canonical.encode()).hexdigest()
        return payload
