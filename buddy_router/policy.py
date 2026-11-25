"""Permission middleware for advisory routes. Fail closed; no operation execution."""
from dataclasses import dataclass

@dataclass(frozen=True)
class PolicyResult:
    allowed: bool
    approval_required: bool
    execution_enabled: bool
    reason: str

RISK_ORDER = {"R0":0,"R1":1,"R2":2,"R3":3}

def authorize(decision: dict, *, owner_approved: bool=False, execution_adapter_enabled: bool=False) -> PolicyResult:
    risk = decision.get("risk_level")
    policy = decision.get("policy")
    if risk not in RISK_ORDER:
        return PolicyResult(False, True, False, "Unknown risk level: fail closed")
    if policy == "deny":
        return PolicyResult(False, False, False, "Router denied the request")
    if risk in ("R0", "R1") and policy == "allow_advisory":
        return PolicyResult(True, False, False, "Advisory route authorized; no action execution")
    if policy == "approval_required":
        if not owner_approved:
            return PolicyResult(False, True, False, "Owner approval is required")
        if not execution_adapter_enabled:
            return PolicyResult(False, True, False, "Approval received, but reviewed adapter remains disabled")
        return PolicyResult(False, True, False, "No execution path is implemented in this prototype")
    return PolicyResult(False, True, False, "Unsupported policy: fail closed")
