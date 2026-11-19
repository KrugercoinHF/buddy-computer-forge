from typing import Protocol
from .models import VerifiedApproval


class GitHostAdapter(Protocol):
    def list_open_issues(self, repository: str) -> list[dict]: ...
    def list_pull_requests(self, repository: str) -> list[dict]: ...
    def create_branch(self, repository: str, branch: str, base: str) -> str: ...
    def open_draft_pull_request(self, repository: str, head: str, base: str, title: str, body: str) -> str: ...


class CodingAgent(Protocol):
    def propose_patch(self, repository_snapshot: dict, task: dict) -> dict:
        """Return a patch proposal and rationale; never receive host credentials."""
        ...


class ApprovalGateway(Protocol):
    """Trusted service boundary; implementations must verify signatures and prevent token replay."""

    def verify_approval(
        self,
        approval_token: str,
        proposal_digest: str,
        approved_scope: tuple[str, ...],
    ) -> VerifiedApproval | None:
        """Return verified identity/evidence, or None. Never trust caller-supplied identity strings."""
        ...
