"""Transparent choice selection; this module recommends, it never executes tools."""
from __future__ import annotations
from .models import ActionOption, CitizenProfile, DecisionRecord

RISK = {"R0": 0, "R1": 1, "R2": 2, "R3": 3}

def choose_action(citizen: CitizenProfile, options: list[ActionOption]) -> DecisionRecord:
    """Choose the best permitted option and emit an auditable decision summary.

    This is a bounded decision policy, not a claim of consciousness or a dump of
    private model chain-of-thought. Any model-based deliberation belongs behind
    a separately permissioned adapter and must return evidence/structured reasons.
    """
    if citizen.autonomy == "observe":
        return DecisionRecord(citizen.id, None, "OBSERVE_ONLY", "Citizen is configured for observation only.", ("Autonomy policy prohibits recommendations and actions.",))
    eligible: list[tuple[float, ActionOption, tuple[str, ...]]] = []
    rejected: list[dict[str, str]] = []
    scorecard: list[dict[str, float | str]] = []
    for option in options:
        missing = option.required_capabilities - citizen.capabilities
        if missing:
            rejected.append({"option": option.id, "reason": "Missing capabilities: " + ", ".join(sorted(missing))})
            continue
        if RISK[option.risk] > RISK[citizen.max_risk]:
            rejected.append({"option": option.id, "reason": f"Risk {option.risk} exceeds citizen ceiling {citizen.max_risk}"})
            continue
        alignment = len(set(option.value_alignment) & set(citizen.values))
        score = (option.estimated_value * option.confidence) - option.estimated_cost + alignment * 0.25
        eligible.append((score, option, (f"Expected-value estimate: {option.estimated_value:.2f} × confidence {option.confidence:.2f}.", f"Estimated cost: {option.estimated_cost:.2f}.", f"Value alignment matches: {alignment}.")))
        scorecard.append({"option": option.id, "score": round(score, 4), "confidence": option.confidence})
    if not eligible:
        return DecisionRecord(citizen.id, None, "NO_SAFE_OPTION", "No option satisfies the citizen's declared capability and risk boundaries.", ("Fail-closed: no eligible option.",), tuple(rejected), tuple(scorecard))
    eligible.sort(key=lambda item: (-item[0], item[1].id))
    _, chosen, reasons = eligible[0]
    approval = chosen.risk in ("R2", "R3") or chosen.external_effect or chosen.irreversible
    disposition = "APPROVAL_REQUIRED" if approval else "RECOMMEND"
    if citizen.autonomy == "reversible_internal" and (chosen.external_effect or chosen.irreversible or chosen.risk != "R0"):
        disposition = "APPROVAL_REQUIRED"
    summary = f"{citizen.name} selected '{chosen.id}' as the strongest eligible option; this is a recommendation, not execution."
    return DecisionRecord(citizen.id, chosen.id, disposition, summary, reasons + (("Owner approval is required before any consequential action.",) if approval else ("Option is advisory; no operation was executed.",)), tuple(rejected), tuple(scorecard), chosen.evidence_refs, False)
