from fastapi.testclient import TestClient

from buddy.ui_app import app


def test_nodes_dashboard_is_served():
    with TestClient(app) as client:
        response = client.get("/nodes")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Node management" in response.text
    assert "Registered workers" in response.text


def test_nodes_dashboard_sets_security_headers():
    with TestClient(app) as client:
        response = client.get("/nodes")

    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "default-src 'none'" in response.headers["content-security-policy"]
    assert "connect-src 'self'" in response.headers["content-security-policy"]
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_nodes_dashboard_contains_required_controls():
    with TestClient(app) as client:
        response = client.get("/nodes")
    html = response.text

    for marker in (
        'id="token"',
        'id="invite"',
        'id="node"',
        'id="name"',
        'id="ttl"',
        'id="rows"',
        'id="refresh"',
        "rotate-token",
        "revoke",
        "copy",
    ):
        assert marker in html


def test_nodes_dashboard_does_not_embed_secrets():
    with TestClient(app) as client:
        response = client.get("/nodes")
    html = response.text

    assert "BUDDY_OWNER_TOKEN" not in html
    assert "node_token" not in html
    assert "enrollment_code" not in html


def test_nodes_dashboard_uses_safe_text_rendering():
    with TestClient(app) as client:
        response = client.get("/nodes")
    html = response.text

    assert "textContent" in html
    assert "innerHTML" not in html


def test_ui_app_includes_core_and_dashboard_routes():
    with TestClient(app) as client:
        health = client.get("/api/health")
        dashboard = client.get("/nodes")

    assert health.status_code == 200
    assert health.json()["features"]["owner_issued_node_enrollment"] is True
    assert dashboard.status_code == 200
