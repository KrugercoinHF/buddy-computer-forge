from digital_citizens import ActionOption, CitizenProfile, choose_action

def citizen(**overrides):
    values = dict(id="mira", name="Mira", role="Engineer", values=("safety", "quality"), capabilities=frozenset({"read", "draft"}), max_risk="R1")
    values.update(overrides)
    return CitizenProfile(**values)

def test_selects_best_eligible_option_and_explains_choice():
    result = choose_action(citizen(), [
        ActionOption("a", "Read docs", frozenset({"read"}), estimated_value=3, confidence=.9),
        ActionOption("b", "Draft test plan", frozenset({"draft"}), estimated_value=5, confidence=.9, value_alignment=("quality",)),
    ])
    assert result.selected_action_id == "b"
    assert result.disposition == "RECOMMEND"
    assert result.execution_performed is False
    assert result.reasons

def test_capability_mismatch_is_rejected():
    result = choose_action(citizen(), [ActionOption("x", "Send email", frozenset({"email_send"}), risk="R1")])
    assert result.disposition == "NO_SAFE_OPTION"
    assert "Missing capabilities" in result.rejected_options[0]["reason"]

def test_risk_ceiling_fails_closed():
    result = choose_action(citizen(), [ActionOption("x", "Deploy", risk="R3")])
    assert result.disposition == "NO_SAFE_OPTION"

def test_external_or_irreversible_action_needs_owner_approval():
    result = choose_action(citizen(max_risk="R3"), [ActionOption("x", "Publish", risk="R3", external_effect=True)])
    assert result.disposition == "APPROVAL_REQUIRED"
    assert result.execution_performed is False

def test_observe_only_citizen_does_not_choose():
    result = choose_action(citizen(autonomy="observe"), [ActionOption("x", "Read", estimated_value=10)])
    assert result.disposition == "OBSERVE_ONLY"
    assert result.selected_action_id is None

def test_missing_options_fail_closed():
    result = choose_action(citizen(), [])
    assert result.disposition == "NO_SAFE_OPTION"
