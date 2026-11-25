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

    # A requested profile is an identifier, never a registry record. Validate
    # its type and membership before using it as a dictionary key.
    chosen = request.get("requested_profile")
    if chosen is None:
        profile_id = next(
            (profile_id for profile_id, spec in REGISTRY.items() if intent in spec["intents"]),
            None,
        )
    elif not isinstance(chosen, str) or not chosen.strip():
        return asdict(Decision(
            trace, intent, None, "R1", "deny",
            "requested_profile must be a non-empty registered profile identifier", [], False,
        ))
    elif chosen not in REGISTRY:
        return asdict(Decision(
            trace, intent, None, "R1", "deny",
            "Requested profile is not registered", [], False,
        ))
    else:
        profile_id = chosen

    if profile_id is None:
        return asdict(Decision(
            trace, intent, None, "R1", "deny",
            "No registered profile matches this intent", [], False,
        ))

    spec = REGISTRY[profile_id]
    risk = spec["risk"]

    # Intent compatibility must be checked before special risk/disabled
    # handling; a mismatched request is a denial, not an approval request.
    if intent not in spec["intents"]:
        return asdict(Decision(
            trace, intent, profile_id, risk, "deny",
            "Requested profile does not support this intent", [], False,
        ))

    if profile_id in DISABLED:
        return asdict(Decision(
            trace, intent, profile_id, risk, "approval_required",
            "Profile is disabled for execution; approval and a separately reviewed adapter would be required",
            spec["capabilities"], False,
        ))

    policy = "allow_advisory" if risk in ("R0", "R1") else "approval_required"
    reason = (
        "Advisory routing only; no execution"
        if policy == "allow_advisory"
        else "Consequential operation requires explicit owner approval"
    )
    return asdict(Decision(
        trace, intent, profile_id, risk, policy, reason, spec["capabilities"], False,
    ))
