import pytest
from fastapi.testclient import TestClient

from app.main import app


class _FakeUser:
    def __init__(self, admin=False):
        self.role_codes = ["platform_admin"] if admin else ["member"]
        self.email = "admin@example.com" if admin else "user@example.com"
        self.memberships = []


@pytest.fixture
def client():
    return TestClient(app)


def test_ops_health_ok(client):
    r = client.get("/api/v1/ops/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ops_ready_ok(client):
    r = client.get("/api/v1/ops/ready")
    assert r.status_code in (200, 503)
    assert "status" in r.json()


def test_ops_details_admin(client):
    from app.shared.presentation.auth_dependencies import require_current_user

    app.dependency_overrides[require_current_user] = lambda: _FakeUser(admin=True)
    r = client.get("/api/v1/ops/details")
    app.dependency_overrides.clear()
    assert r.status_code in (200, 503)
    body = r.json()
    assert "health" in body and "readiness" in body


def test_ops_details_forbidden(client):
    from app.shared.presentation.auth_dependencies import require_current_user

    app.dependency_overrides[require_current_user] = lambda: _FakeUser(admin=False)
    r = client.get("/api/v1/ops/details")
    app.dependency_overrides.clear()
    assert r.status_code == 403


def test_metrics_disabled(client, monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.settings, "ENABLE_METRICS", False)
    r = client.get("/api/v1/metrics")
    assert r.status_code == 404


def test_metrics_forbidden(client, monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.settings, "ENABLE_METRICS", True)
    monkeypatch.setattr(config.settings, "METRICS_ALLOWED_IPS", "10.0.0.1")
    r = client.get("/api/v1/metrics")
    assert r.status_code == 403


def test_metrics_ok(client, monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.settings, "ENABLE_METRICS", True)
    monkeypatch.setattr(config.settings, "METRICS_ALLOWED_IPS", "127.0.0.1")
    r = client.get("/api/v1/metrics", headers={"x-forwarded-for": "127.0.0.1"})
    assert r.status_code == 200
    assert "text/plain" in r.headers.get("content-type", "")
