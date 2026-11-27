from bot_departments.api import route, departments, RouteRequest, require_department_owner
from fastapi import HTTPException


def test_api_route_advisory():
    result = route(RouteRequest(task="research renewable energy"), None)
    assert result["department"] == "research"
    assert result["advisory_only"] is True
    assert result["execution_enabled"] is False


def test_disabled_department_api_denies():
    result = route(RouteRequest(task="operate computer", department="computer"), None)
    assert result["decision"] == "DENY_DISABLED"


def test_auth_missing_rejected(monkeypatch):
    monkeypatch.setenv("BUDDY_OWNER_TOKEN", "test-token")
    try:
        require_department_owner(None)
    except HTTPException as exc:
        assert exc.status_code == 401
    else:
        assert False, "missing auth must be rejected"


def test_auth_valid(monkeypatch):
    monkeypatch.setenv("BUDDY_OWNER_TOKEN", "test-token")
    assert require_department_owner("Bearer test-token") is None
