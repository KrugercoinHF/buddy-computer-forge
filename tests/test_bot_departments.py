from bot_departments.router import route_task, load_registry, RoutingError

def test_research_routes():
    assert route_task("research renewable energy")['department'] == "research"

def test_manual_department_selection():
    assert route_task("help", "finance")['department'] == "finance"

def test_unknown_department_rejected():
    try: route_task("help", "bogus")
    except RoutingError: pass
    else: assert False

def test_computer_department_disabled():
    result = route_task("operate my computer", "computer")
    assert result['decision'] == "DENY_DISABLED"
    assert result['execution_enabled'] is not True

def test_advisory_only_and_approval_boundary():
    result = route_task("build code")
    assert result['advisory_only'] is True
    assert result['execution_enabled'] is False
    assert result['approval_required_for_consequential_actions'] is True

def test_registry_ids_unique():
    data=load_registry(); ids=[d['id'] for d in data['departments']]
    assert len(ids)==len(set(ids))
