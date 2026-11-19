import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .adapters import ApprovalGateway
from .models import Finding, WorkProposal
from .policy import MaintainerPolicy


class RepositoryMaintainer:
    """Read-only Git inspection and approval evidence bound to an exact proposal."""

    def __init__(
        self,
        root: str | Path,
        repository: str,
        policy: MaintainerPolicy,
        approval_gateway: ApprovalGateway | None = None,
    ):
        self.root = Path(root).resolve()
        self.repository = repository
        self.policy = policy
        self.approval_gateway = approval_gateway
        if not self.root.is_dir():
            raise ValueError("repository root must be an existing directory")
        self.policy.validate_repository(repository)

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=self.root, text=True, capture_output=True, check=True
        )
        return result.stdout.strip()

    def inspect(self) -> dict:
        branch = self._git("branch", "--show-current")
        head = self._git("rev-parse", "HEAD")
        status = self._git("status", "--porcelain=v1")
        tracked = self._git("ls-files").splitlines()
        paths = set(tracked)
        findings: list[Finding] = []
        if "README.md" not in paths:
            findings.append(Finding("repo.readme.missing", "medium", "README is missing",
                                    "Add setup, test and contribution guidance.", "README.md"))
        if not any(p.startswith(("tests/", "test/")) or p.startswith("tests\\") for p in paths):
            findings.append(Finding("repo.tests.missing", "high", "No tracked test directory found",
                                    "Add automated tests before enabling autonomous code changes."))
        if not any(p.startswith(".github/workflows/") for p in paths):
            findings.append(Finding("repo.ci.missing", "high", "No GitHub Actions workflow found",
                                    "Add CI for tests, lint and security checks."))
        if status:
            findings.append(Finding("repo.worktree.dirty", "high", "Working tree is not clean",
                                    "Do not overwrite or mix uncommitted human changes."))
        return {
            "repository": self.repository,
            "root": str(self.root),
            "branch": branch,
            "head": head,
            "clean_worktree": not bool(status),
            "tracked_files": len(tracked),
            "findings": [f.__dict__ for f in findings],
        }

    def propose(self, base_ref: str = "main") -> WorkProposal:
        self.policy.validate_base(base_ref)
        report = self.inspect()
        findings = tuple(Finding(**item) for item in report["findings"])
        raw = self.repository + report["head"] + json.dumps(report["findings"], sort_keys=True)
        digest = hashlib.sha256(raw.encode()).hexdigest()[:12]
        return WorkProposal(
            f"repo-maint-{digest}", self.repository, base_ref, f"agent/repo-maint-{digest}",
            f"Repository inspection found {len(findings)} maintenance item(s); proposal only.",
            findings, ("python -m pytest", "ruff check .", "bandit -r ."),
        )

    @staticmethod
    def proposal_digest(proposal: WorkProposal) -> str:
        canonical = json.dumps(proposal.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def record_approval(
        self,
        proposal: WorkProposal,
        approval_token: str,
        approved_scope: tuple[str, ...],
    ) -> dict:
        """Record only gateway-verified approval; this method never authenticates a name."""
        if self.approval_gateway is None:
            raise PermissionError("a trusted approval gateway is required")
        if not approval_token or not approved_scope:
            raise PermissionError("approval token and explicit non-empty scope are required")

        digest = self.proposal_digest(proposal)
        verified = self.approval_gateway.verify_approval(
            approval_token=approval_token,
            proposal_digest=digest,
            approved_scope=approved_scope,
        )
        if verified is None:
            raise PermissionError("approval gateway rejected or could not verify the token")
        if (
            not verified.subject.strip()
            or not verified.token_id.strip()
            or not verified.verifier.strip()
            or verified.proposal_digest != digest
            or set(verified.approved_scope) != set(approved_scope)
        ):
            raise PermissionError("verified approval does not match this proposal and scope")
        try:
            expiry = datetime.fromisoformat(verified.expires_at.replace("Z", "+00:00"))
        except (TypeError, ValueError) as exc:
            raise PermissionError("approval expiry is invalid") from exc
        if expiry.tzinfo is None or expiry <= datetime.now(timezone.utc):
            raise PermissionError("approval is expired or has no timezone")

        payload = {
            "proposal": proposal.to_dict(),
            "proposal_digest": digest,
            "approver": verified.subject,
            "approved_scope": list(verified.approved_scope),
            "approval_token_id": verified.token_id,
            "approval_expires_at": verified.expires_at,
            "verified_by": verified.verifier,
            "decision": "approved",
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        payload["approval_record_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return payload
