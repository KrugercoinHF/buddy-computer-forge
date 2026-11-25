"""Deterministic, advisory-only routing prototype. No tools are executed."""
from dataclasses import dataclass, asdict
from typing import Any

REGISTRY = {
    "buddybot": {"intents": ["personal_assistance"], "risk": "R0", "capabilities": ["conversation"]},
    "grokbot": {"intents": ["research_and_summarize", "coding_assistance"], "risk": "R0", "capabilities": ["reasoning", "research_draft"]},
    "manus-patterns": {"intents": ["plan_task"], "risk": "R1", "capabilities": ["planning"]},
    "battlemind": {"intents": ["evaluate_solution"], "risk": "R1", "capabilities": ["evaluation"]},
    "ai-boardroom": {"intents": ["simulate_boardroom"], "risk": "R1", "capabilities": ["deliberation_simulation"]},
    "computer-forge": {"intents": ["computer_operation_request"], "risk": "R3", "capabilities": ["computer_operation_request"]},
    "autogenius": {"intents": ["discover_capabilities"], "risk": "R0", "capabilities": ["registry_lookup"]},
}
DISABLED = {"computer-forge"}

@dataclass
class Decision:
    trace_id: str
    intent: str
    profile_id: str | None
    risk_level: str
    policy: str
    reason: str
    capabilities: list[str]
    execution_enabled: bool = False

def route(request: dict[str, Any]) -> dict[str, Any]:
    trace = str(request.get("trace_id", ""))
    intent = str(request.get("intent", ""))
    if not trace or not intent:
        return asdict(Decision(trace, intent, None, "R3", "deny", "trace_id and intent are required", [], False))
    chosen = request.get("requested_profile")
    profile = REGISTRY.get(chosen) if chosen else next((p for p in REGISTRY if intent in REGISTRY[p]["intents"]), None)
    if not profile:
        return asdict(Decision(trace, intent, None, "R1", "deny", "No registered profile matches this intent", [], False))
    spec = REGISTRY[profile]
    risk = spec["risk"]
    if profile in DISABLED:
        return asdict(Decision(trace, intent, profile, risk, "approval_required", "Profile is disabled for execution; approval and a separately reviewed adapter would be required", spec["capabilities"], False))
    if chosen and intent not in spec["intents"]:
        return asdict(Decision(trace, intent, profile, risk, "deny", "Requested profile does not support this intent", [], False))
    policy = "allow_advisory" if risk in ("R0", "R1") else "approval_required"
    reason = "Advisory routing only; no execution" if policy == "allow_advisory" else "Consequential operation requires explicit owner approval"
    return asdict(Decision(trace, intent, profile, risk, policy, reason, spec["capabilities"], False))
