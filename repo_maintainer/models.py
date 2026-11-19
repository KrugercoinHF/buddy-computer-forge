from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    title: str
    detail: str
    path: str | None = None


@dataclass(frozen=True)
class WorkProposal:
    proposal_id: str
    repository: str
    base_ref: str
    suggested_branch: str
    summary: str
    findings: tuple[Finding, ...] = ()
    suggested_checks: tuple[str, ...] = ()
    requires_owner_approval: bool = True
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VerifiedApproval:
    """Identity and scope returned only after an external gateway verifies a signed approval."""
    subject: str
    proposal_digest: str
    approved_scope: tuple[str, ...]
    token_id: str
    expires_at: str
    verifier: str
