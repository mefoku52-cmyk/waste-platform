from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.presentation.dependencies import (
    get_login_service,
    get_logout_service,
    get_refresh_token_service,
)

ORIGIN = "http://localhost:3000"
COOKIE_DOMAIN = "testserver.local"
COOKIE_PATH = "/api/v1/auth/browser"


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_browser_login_uses_httponly_refresh_cookie_without_json_refresh_token(client):
    login_service = SimpleNamespace(
        execute=AsyncMock(
            return_value=SimpleNamespace(
                requires_2fa=False,
                access_token="access-browser",
                refresh_token="refresh-secret",
                token_type="Bearer",
                expires_in=900,
            )
        )
    )
    app.dependency_overrides[get_login_service] = lambda: login_service

    response = client.post(
        "/api/v1/auth/browser/login",
        json={"email": "user@example.com", "password": "password123"},
        headers={"Origin": ORIGIN},
    )

    assert response.status_code == 200, response.text
    assert response.json()["accessToken"] == "access-browser"
    assert "refreshToken" not in response.json()
    assert response.json()["csrfToken"]
    assert response.cookies.get("cmep_browser_refresh") == "refresh-secret"
    assert response.cookies.get("cmep_browser_csrf") == response.json()["csrfToken"]
    refresh_header = next(
        value for value in response.headers.get_list("set-cookie")
        if value.startswith("cmep_browser_refresh=")
    )
    assert "httponly" in refresh_header.lower()
    assert f"path={COOKIE_PATH}" in refresh_header.lower()
    assert "refresh-secret" not in response.text


def test_browser_refresh_requires_matching_csrf_and_rotates_cookie(client):
    refresh_service = SimpleNamespace(
        execute=AsyncMock(
            return_value=SimpleNamespace(
                access_token="access-rotated",
                refresh_token="refresh-rotated",
                token_type="Bearer",
                expires_in=900,
            )
        )
    )
    app.dependency_overrides[get_refresh_token_service] = lambda: refresh_service
    client.cookies.set("cmep_browser_refresh", "refresh-old", domain=COOKIE_DOMAIN, path=COOKIE_PATH)
    client.cookies.set("cmep_browser_csrf", "csrf-old", domain=COOKIE_DOMAIN, path=COOKIE_PATH)

    denied = client.post(
        "/api/v1/auth/browser/refresh",
        headers={"Origin": ORIGIN, "X-CSRF-Token": "wrong"},
    )
    assert denied.status_code == 403
    refresh_service.execute.assert_not_awaited()

    response = client.post(
        "/api/v1/auth/browser/refresh",
        headers={"Origin": ORIGIN, "X-CSRF-Token": "csrf-old"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["accessToken"] == "access-rotated"
    assert "refreshToken" not in response.json()
    assert client.cookies.get(
        "cmep_browser_refresh", domain=COOKIE_DOMAIN, path=COOKIE_PATH
    ) == "refresh-rotated"
    assert response.json()["csrfToken"] != "csrf-old"
    refresh_service.execute.assert_awaited_once_with(refresh_token="refresh-old")


def test_browser_csrf_nonce_refuses_unconfigured_origin(client):
    response = client.get(
        "/api/v1/auth/browser/csrf",
        headers={"Origin": "https://attacker.invalid"},
    )
    assert response.status_code == 403
    assert "cmep_browser_csrf" not in response.cookies


def test_browser_logout_requires_csrf_before_revoking_refresh_cookie(client):
    logout_service = SimpleNamespace(execute=AsyncMock())
    app.dependency_overrides[get_logout_service] = lambda: logout_service
    client.cookies.set("cmep_browser_refresh", "refresh-old", domain=COOKIE_DOMAIN, path=COOKIE_PATH)
    client.cookies.set("cmep_browser_csrf", "csrf-old", domain=COOKIE_DOMAIN, path=COOKIE_PATH)

    denied = client.post(
        "/api/v1/auth/browser/logout",
        headers={"Origin": ORIGIN, "X-CSRF-Token": "bad"},
    )
    assert denied.status_code == 403
    logout_service.execute.assert_not_awaited()

    response = client.post(
        "/api/v1/auth/browser/logout",
        headers={"Origin": ORIGIN, "X-CSRF-Token": "csrf-old"},
    )
    assert response.status_code == 204
    logout_service.execute.assert_awaited_once_with(refresh_token="refresh-old")
    assert client.cookies.get(
        "cmep_browser_refresh", domain=COOKIE_DOMAIN, path=COOKIE_PATH
    ) is None



def test_browser_csrf_endpoint_is_rate_limited(client):
    with patch(
        "app.shared.infrastructure.rate_limit.check_rate_limit", new_callable=AsyncMock
    ) as check:
        response = client.get(
            "/api/v1/auth/browser/csrf",
            headers={"Origin": ORIGIN},
        )
    assert response.status_code == 200, response.text
    assert check.await_count == 2
    assert all(
        call.args[0].startswith("auth-browser:csrf:")
        for call in check.await_args_list
    )


def test_browser_refresh_and_logout_have_route_rate_limits(client):
    refresh_service = SimpleNamespace(
        execute=AsyncMock(
            return_value=SimpleNamespace(
                access_token="access-next",
                refresh_token="refresh-next",
                token_type="Bearer",
                expires_in=900,
            )
        )
    )
    logout_service = SimpleNamespace(execute=AsyncMock())
    app.dependency_overrides[get_refresh_token_service] = lambda: refresh_service
    app.dependency_overrides[get_logout_service] = lambda: logout_service
    client.cookies.set("cmep_browser_refresh", "refresh-old", domain=COOKIE_DOMAIN, path=COOKIE_PATH)
    client.cookies.set("cmep_browser_csrf", "csrf-old", domain=COOKIE_DOMAIN, path=COOKIE_PATH)

    with patch(
        "app.shared.infrastructure.rate_limit.check_rate_limit", new_callable=AsyncMock
    ) as check:
        refreshed = client.post(
            "/api/v1/auth/browser/refresh",
            headers={"Origin": ORIGIN, "X-CSRF-Token": "csrf-old"},
        )
        new_csrf = refreshed.json()["csrfToken"]
        logged_out = client.post(
            "/api/v1/auth/browser/logout",
            headers={"Origin": ORIGIN, "X-CSRF-Token": new_csrf},
        )

    assert refreshed.status_code == 200, refreshed.text
    assert logged_out.status_code == 204
    keys = [call.args[0] for call in check.await_args_list]
    assert any(key.startswith("auth-browser:refresh:") for key in keys)
    assert any(key.startswith("auth-browser:logout:") for key in keys)


def test_cookie_security_and_lifetime_match_refresh_token(monkeypatch):
    from app.core.config import settings
    from app.modules.auth.presentation.router import (
        _browser_cookie_options,
        _browser_refresh_max_age,
    )

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AUTH_COOKIE_SAMESITE", "lax")
    monkeypatch.setenv("AUTH_REFRESH_COOKIE_MAX_AGE_SECONDS", "99999999")
    options = _browser_cookie_options()
    assert options["httponly"] is True
    assert options["secure"] is True
    assert options["samesite"] == "lax"
    assert options["path"] == COOKIE_PATH
    assert _browser_refresh_max_age() <= settings.jwt.refresh_token_expire_days * 24 * 60 * 60


def test_samesite_none_forces_secure_cookie(monkeypatch):
    from app.modules.auth.presentation.router import _browser_cookie_options

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("AUTH_COOKIE_SAMESITE", "none")
    assert _browser_cookie_options()["secure"] is True
