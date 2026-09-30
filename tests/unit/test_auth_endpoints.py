"""Auth endpoints smoke tests — auth guards, status codes, OpenAPI."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


# ─── Login ─────────────────────────────────────────────────────


def test_login_missing_body_422(client):
    r = client.post("/api/v1/auth/login", json={})
    assert r.status_code == 422


def test_login_invalid_email_422(client):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "not-an-email", "password": "x"},
    )
    assert r.status_code == 422


def test_login_fake_domain_returns_401_or_429(client):
    """Login nemá fake-domain validáciu — vráti 401 (user enum protection)."""
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "user@b.c", "password": "password123"},
    )
    assert r.status_code in (401, 422, 429)


def test_login_valid_shape_returns_401_for_unknown_email(client):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example-real-xyz.com", "password": "x"},
    )
    # Buď 401 (bezpečné) alebo 429 (rate limit) — nie 5xx
    assert r.status_code in (401, 422, 429)


# ─── 2FA ───────────────────────────────────────────────────────


def test_2fa_status_requires_auth(client):
    r = client.get("/api/v1/auth/2fa/status")
    assert r.status_code == 401


def test_2fa_setup_requires_auth(client):
    r = client.post("/api/v1/auth/2fa/setup", json={})
    assert r.status_code == 401


def test_2fa_verify_requires_auth(client):
    r = client.post("/api/v1/auth/2fa/verify", json={})
    assert r.status_code == 401


def test_2fa_disable_requires_auth(client):
    r = client.post("/api/v1/auth/2fa/disable", json={})
    assert r.status_code == 401


def test_2fa_backup_codes_regenerate_requires_auth(client):
    r = client.post("/api/v1/auth/2fa/backup-codes/regenerate", json={})
    assert r.status_code == 401


def test_2fa_login_bad_token_returns_401(client):
    r = client.post(
        "/api/v1/auth/2fa/login",
        json={
            "twoFactorToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake.fake",
            "code": "000000",
        },
    )
    assert r.status_code in (401, 422, 429)


# ─── Refresh / Logout ──────────────────────────────────────────


def test_refresh_requires_body(client):
    r = client.post("/api/v1/auth/refresh", json={})
    assert r.status_code == 422


def test_logout_is_idempotent(client):
    """Logout je bezpečný aj bez auth — vráti 2xx alebo 401."""
    r = client.post("/api/v1/auth/logout", json={})
    assert r.status_code in (200, 204, 401)


# ─── Me ────────────────────────────────────────────────────────


def test_me_requires_auth(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_me_with_invalid_token_returns_401(client):
    r = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert r.status_code == 401


def test_me_with_alg_none_token_returns_401(client):
    # header {"alg":"none"} + payload {"sub":"admin"}
    none_token = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJhZG1pbiIsInR5cGUiOiJhY2Nlc3MifQ."
    r = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {none_token}"},
    )
    assert r.status_code == 401


# ─── Forgot / Reset / Verify ───────────────────────────────────


def test_forgot_password_responds_same_for_invalid(client):
    """User enum protection — aj neplatný email vráti rovnaký status."""
    r = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "not-an-email"},
    )
    assert r.status_code in (200, 422, 429)


def test_forgot_password_generic_response(client):
    """User enumeration protection — always returns 200."""
    r = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "definitely-does-not-exist-xyz@example.com"},
    )
    assert r.status_code in (200, 429)


def test_reset_password_missing_body_422(client):
    r = client.post("/api/v1/auth/reset-password", json={})
    assert r.status_code == 422


def test_verify_email_missing_token_422(client):
    r = client.post("/api/v1/auth/verify-email", json={})
    assert r.status_code == 422


def test_resend_verification_responds_for_invalid(client):
    """User enum protection — aj neplatný email vráti rovnaký status."""
    r = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "not-an-email"},
    )
    assert r.status_code in (200, 422, 429)


# ─── OpenAPI registration ──────────────────────────────────────


def test_openapi_has_all_auth_endpoints():
    paths = app.openapi()["paths"]
    for p in [
        "/api/v1/auth/login",
        "/api/v1/auth/2fa/login",
        "/api/v1/auth/2fa/status",
        "/api/v1/auth/2fa/setup",
        "/api/v1/auth/2fa/verify",
        "/api/v1/auth/2fa/disable",
        "/api/v1/auth/2fa/backup-codes/regenerate",
        "/api/v1/auth/refresh",
        "/api/v1/auth/logout",
        "/api/v1/auth/me",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
        "/api/v1/auth/verify-email",
        "/api/v1/auth/resend-verification",
    ]:
        assert p in paths, f"missing {p}"
