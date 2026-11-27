"""Deterministic advisory routing across Buddy Agency bot departments.
No provider or tool execution occurs here; routing is an inspectable recommendation.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

REGISTRY = Path(__file__).with_name("registry.json")
RISK_ORDER = {"R0": 0, "R1": 1, "R2": 2, "R3": 3}

class RoutingError(ValueError):
    pass

def load_registry(path: Path = REGISTRY) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    ids = [d["id"] for d in data["departments"]]
    if len(ids) != len(set(ids)):
        raise RoutingError("Duplicate department IDs")
    return data

def route_task(task: str, department: str | None = None, *, registry: dict[str, Any] | None = None) -> dict[str, Any]:
    if not task or not task.strip():
        raise RoutingError("Task text is required")
    data = registry or load_registry()
    departments = {d["id"]: d for d in data["departments"]}
    if department:
        selected = departments.get(department)
        if not selected:
            raise RoutingError(f"Unknown department: {department}")
        reason = "Owner/menu-selected department"
    else:
        text = task.casefold()
        rules = [("research", ("research", "find", "compare", "investigate", "summarize")),
                 ("engineering", ("code", "repo", "github", "build", "test", "debug")),
                 ("boardroom", ("boardroom", "decision", "strategy", "deliberate")),
                 ("knowledge", ("memory", "knowledge", "remember", "document")),
                 ("battle", ("benchmark", "evaluate", "critique", "quality", "compare models")),
                 ("operations", ("monitor", "automation", "schedule", "workflow", "mission")),
                 ("finance", ("budget", "finance", "business", "profit", "cost")),
                 ("communications", ("email", "message", "write", "draft", "content"))]
        selected = departments["executive"]
        reason = "No strong intent match; executive intake" 
        for dep, words in rules:
            if any(w in text for w in words):
                selected, reason = departments[dep], f"Matched {dep} intent keywords"
                break
    if not selected["enabled"]:
        return {"department": selected["id"], "name": selected["name"], "decision": "DENY_DISABLED",
                "risk_ceiling": selected["risk_ceiling"], "capabilities": [], "reason": "Department disabled; no fallback execution", "advisory_only": True, "execution_enabled": False}
    return {"department": selected["id"], "name": selected["name"], "decision": "ROUTE_ADVISORY",
            "risk_ceiling": selected["risk_ceiling"], "capabilities": selected["capabilities"],
            "profiles": selected["profiles"], "reason": reason, "advisory_only": True,
            "execution_enabled": False, "approval_required_for_consequential_actions": True}
