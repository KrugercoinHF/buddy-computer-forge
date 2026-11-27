"""Typed contracts for identity, goals, bounded actions and decisions."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

Risk = Literal["R0", "R1", "R2", "R3"]
Autonomy = Literal["observe", "recommend", "reversible_internal"]

@dataclass(frozen=True)
class CitizenProfile:
    id: str
    name: str
    role: str
    personality: tuple[str, ...] = ()
    values: tuple[str, ...] = ()
    goals: tuple[str, ...] = ()
    capabilities: frozenset[str] = frozenset()
    autonomy: Autonomy = "recommend"
    max_risk: Risk = "R1"
    memory_scope: Literal["none", "session", "project", "owner-approved-shared"] = "session"

    def __post_init__(self) -> None:
        if not self.id or not self.id.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Citizen id must be a non-empty stable identifier")
        if not self.name.strip() or not self.role.strip():
            raise ValueError("Citizen name and role are required")
        if self.autonomy not in ("observe", "recommend", "reversible_internal"):
            raise ValueError("Unsupported autonomy level")

@dataclass(frozen=True)
class ActionOption:
    id: str
    description: str
    required_capabilities: frozenset[str] = frozenset()
    risk: Risk = "R0"
    estimated_value: float = 0.0
    estimated_cost: float = 0.0
    confidence: float = 0.5
    value_alignment: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    external_effect: bool = False
    irreversible: bool = False

    def __post_init__(self) -> None:
        if not self.id or not self.description.strip():
            raise ValueError("Action id and description are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.estimated_cost < 0:
            raise ValueError("estimated_cost cannot be negative")

@dataclass(frozen=True)
class DecisionRecord:
    citizen_id: str
    selected_action_id: str | None
    disposition: Literal["RECOMMEND", "APPROVAL_REQUIRED", "NO_SAFE_OPTION", "OBSERVE_ONLY"]
    summary: str
    reasons: tuple[str, ...]
    rejected_options: tuple[dict[str, str], ...] = ()
    scorecard: tuple[dict[str, float | str], ...] = ()
    evidence_refs: tuple[str, ...] = ()
    execution_performed: bool = False

@dataclass(frozen=True)
class FeedbackRecord:
    citizen_id: str
    decision_action_id: str
    rating: Literal["helpful", "not_helpful", "unsafe", "incorrect"]
    note: str = ""
    reviewer: str = "owner"
    applied_to_profile: bool = False
