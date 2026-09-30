"""Smoke tests for app.main — routes, middleware, security headers."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_app_loads():
    assert app is not None


def test_health_endpoint_returns_200(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_health_payload_shape(client):
    r = client.get("/health")
    data = r.json()
    assert data.get("status") == "ok"
    assert "service" in data
    assert "version" in data


def test_health_lists_mounted_routers(client):
    r = client.get("/health")
    data = r.json()
    assert "mounted_routers" in data
    assert "shared.api_router" in data["mounted_routers"]


def test_security_headers_on_health(client):
    r = client.get("/health")
    headers = {k.lower(): v for k, v in r.headers.items()}
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert "strict-transport-security" in headers


def test_security_headers_on_404(client):
    r = client.get("/totally-nonexistent-endpoint-xyz")
    assert r.status_code == 404
    headers = {k.lower(): v for k, v in r.headers.items()}
    assert headers.get("x-content-type-options") == "nosniff"


def test_security_headers_on_401(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401
    headers = {k.lower(): v for k, v in r.headers.items()}
    assert headers.get("x-content-type-options") == "nosniff"


def test_unknown_endpoint_returns_404(client):
    r = client.get("/nope-does-not-exist-12345")
    assert r.status_code == 404


def test_wrong_method_returns_405(client):
    r = client.post("/health")
    assert r.status_code == 405


def test_api_prefix_v1_auth_me_requires_auth(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code in (401, 403)


def test_middleware_stack_contains_expected():
    names = [getattr(m.cls, "__name__", str(m.cls)) for m in app.user_middleware]
    assert "CORSMiddleware" in names
    assert "SecurityHeadersMiddleware" in names
    assert "RateLimitMiddleware" in names


def test_no_x_powered_by_header(client):
    r = client.get("/health")
    headers = {k.lower() for k in r.headers}
    assert "x-powered-by" not in headers


def test_cors_preflight_from_trc_cmep(client):
    r = client.options(
        "/api/v1/auth/me",
        headers={
            "Origin": "https://trc-cmep.sk",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert r.status_code in (200, 204)


def test_cors_denies_evil_origin(client):
    r = client.options(
        "/api/v1/auth/me",
        headers={
            "Origin": "https://evil.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    acao = r.headers.get("access-control-allow-origin", "")
    assert "evil.com" not in acao


def test_health_content_type_json(client):
    r = client.get("/health")
    assert "application/json" in r.headers.get("content-type", "")


def test_openapi_schema_generates():
    schema = app.openapi()
    assert "paths" in schema
    assert len(schema["paths"]) > 50
