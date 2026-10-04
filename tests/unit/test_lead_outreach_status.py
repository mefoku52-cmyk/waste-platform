"""GET /admin/lead-outreach/status.

Bezpecnostne pravidlo: odpoved NIKDY nesmie obsahovat hodnotu API kluca
(ani jeho cast, ani dlzku). Vsetko su booly / cisla.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user

URL = "/api/v1/admin/lead-outreach/status"

# Hodnoty, ktore sa NIKDY nesmu objavit v odpovedi.
_FAKE_GROQ = "gsk_THIS_MUST_NEVER_LEAK_1234567890"
_FAKE_RESEND = "re_THIS_MUST_NEVER_LEAK_abcdef"


class _FakeUser:
    class _U:
        email = "admin@cmep.dev"

    user = _U()
    roleCodes: list[str] = []
    memberships: list[object] = []


class _FakeSession:
    """Minimalna session, ktora prezije count_sent_today."""

    async def execute(self, *_args, **_kwargs):
        class _R:
            def scalar(self):
                return 0

        return _R()


async def _fake_db():
    yield _FakeSession()


@pytest.fixture
def client():
    app.dependency_overrides[require_current_user] = lambda: _FakeUser()
    app.dependency_overrides[get_db_session] = _fake_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_status_requires_auth():
    """Bez override = bez tokenu = 401."""
    with TestClient(app) as c:
        r = c.get(URL)
    assert r.status_code == 401


def test_status_returns_200_for_admin(client):
    r = client.get(URL)
    assert r.status_code == 200


def test_status_never_leaks_api_keys(client, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", _FAKE_GROQ)
    monkeypatch.setattr(
        "app.modules.lead_finder.presentation.router.settings.RESEND_API_KEY",
        _FAKE_RESEND,
    )

    r = client.get(URL)
    raw = r.text

    assert _FAKE_GROQ not in raw
    assert _FAKE_RESEND not in raw
    # Ani casti kluca.
    assert "THIS_MUST_NEVER_LEAK" not in raw
    assert "gsk_" not in raw
    assert "re_" not in raw


def test_status_exposes_only_bools_and_numbers(client, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", _FAKE_GROQ)

    payload = client.get(URL).json()

    assert isinstance(payload["outreach_enabled"], bool)
    assert isinstance(payload["ai_fallback_active"], bool)
    assert isinstance(payload["daily_limit"], int)
    assert isinstance(payload["sent_today"], int)
    assert isinstance(payload["remaining_today"], int)

    for key in ("email_provider", "from_email", "ai_provider"):
        block = payload[key]
        assert set(block.keys()) == {"is_set"}
        assert isinstance(block["is_set"], bool)


def test_status_ai_fallback_active_when_key_missing(client, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    payload = client.get(URL).json()

    assert payload["ai_provider"]["is_set"] is False
    assert payload["ai_fallback_active"] is True


def test_status_ai_fallback_inactive_when_key_set(client, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", _FAKE_GROQ)

    payload = client.get(URL).json()

    assert payload["ai_provider"]["is_set"] is True
    assert payload["ai_fallback_active"] is False


def test_status_reflects_resend_key_presence(client, monkeypatch):
    monkeypatch.setattr(
        "app.modules.lead_finder.presentation.router.settings.RESEND_API_KEY",
        "",
    )
    assert client.get(URL).json()["email_provider"]["is_set"] is False

    monkeypatch.setattr(
        "app.modules.lead_finder.presentation.router.settings.RESEND_API_KEY",
        _FAKE_RESEND,
    )
    assert client.get(URL).json()["email_provider"]["is_set"] is True


def test_status_remaining_today_never_negative(client, monkeypatch):
    monkeypatch.setattr(
        "app.modules.lead_finder.presentation.router.count_sent_today",
        _always(999),
    )

    payload = client.get(URL).json()

    assert payload["remaining_today"] == 0


def test_status_openapi_registered():
    schema = app.openapi()
    assert URL in schema["paths"]
    # Len GET — status sa nikdy nemeni.
    assert "get" in schema["paths"][URL]


def _always(value):
    async def _inner(*_args, **_kwargs):
        return value

    return _inner


def test_status_response_is_valid_json(client):
    json.loads(client.get(URL).text)
