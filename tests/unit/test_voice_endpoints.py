"""Voice endpoints (agent-platform voice) — hermetic tests.

Covers transcribe: auth, AI entitlement, content-type allowlist, empty payload,
15 MB cap, mocked provider success/502; and live token endpoint: entitlement,
missing Deepgram key -> 503, mocked failure -> 502, success. No network calls.
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.agent_platform.presentation.dependencies import (
    get_company_entitlement_service,
)
from app.shared.presentation.auth_dependencies import require_current_user

_MP3 = b"\xff\xfb\x90\x64" * 100  # fiktívne MP3 dáta


class _FakeUser:
    def __init__(self, memberships, role_codes=None):
        self.id = str(uuid4())
        self.email = "test@example.com"
        self.isPlatformAdmin = False
        self.memberships = memberships
        self.roleCodes = role_codes or []


class _FakeEntitlements:
    """has_tier() vráti True pre PRO tier iba keď je company_id v pro_ids."""

    def __init__(self, pro_ids):
        self._pro_ids = pro_ids

    async def has_tier(self, company_id, minimum):
        return str(company_id) in self._pro_ids


@pytest.fixture
def client():
    return TestClient(app)


def _override(user, entitlements):
    app.dependency_overrides[require_current_user] = lambda: user
    app.dependency_overrides[get_company_entitlement_service] = lambda: entitlements


@pytest.fixture(autouse=True)
def _cleanup_overrides():
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------- transcribe


def _transcribe(client, content=_MP3, content_type="audio/mpeg", filename="rec.webm"):
    return client.post(
        "/api/v1/agent-platform/voice/transcribe",
        files={"audio": (filename, content, content_type)},
    )


def test_transcribe_requires_auth(client):
    r = _transcribe(client)
    assert r.status_code == 401


def test_transcribe_requires_company(client):
    _override(_FakeUser(memberships=[]), _FakeEntitlements(set()))
    r = _transcribe(client)
    assert r.status_code == 403


def test_transcribe_rejects_without_pro_tier(client):
    _override(_FakeUser(memberships=[{"companyId": "c1"}]), _FakeEntitlements(set()))
    r = _transcribe(client)
    assert r.status_code in {402, 409}


def test_transcribe_rejects_unsupported_content_type(client):
    _override(
        _FakeUser(memberships=[{"companyId": "c1"}]),
        _FakeEntitlements({"c1"}),
    )
    r = _transcribe(client, content_type="text/plain")
    assert r.status_code == 415


def test_transcribe_rejects_empty_payload(client):
    _override(
        _FakeUser(memberships=[{"companyId": "c1"}]),
        _FakeEntitlements({"c1"}),
    )
    r = _transcribe(client, content=b"")
    assert r.status_code == 400


def test_transcribe_rejects_oversized_payload(client):
    _override(
        _FakeUser(memberships=[{"companyId": "c1"}]),
        _FakeEntitlements({"c1"}),
    )
    big = b"\xff" * (15 * 1024 * 1024 + 1)
    r = _transcribe(client, content=big)
    assert r.status_code == 413


def test_transcribe_ok_with_mocked_provider(client):
    _override(
        _FakeUser(memberships=[{"companyId": "c1"}]),
        _FakeEntitlements({"c1"}),
    )
    with patch(
        "app.modules.agent_platform.presentation.voice_router.transcribe_with_mai",
        new=AsyncMock(return_value={"text": "Dobrý deň, volám sa."}),
    ) as m:
        r = _transcribe(client)

    assert r.status_code == 200, r.text
    assert r.json() == {"text": "Dobrý deň, volám sa."}
    m.assert_awaited_once()
    assert m.await_args is not None
    args, _kwargs = m.await_args
    assert args[0] == _MP3


def test_transcribe_provider_failure_is_502(client):
    _override(
        _FakeUser(memberships=[{"companyId": "c1"}]),
        _FakeEntitlements({"c1"}),
    )
    with patch(
        "app.modules.agent_platform.presentation.voice_router.transcribe_with_mai",
        new=AsyncMock(side_effect=RuntimeError("boom")),
    ):
        r = _transcribe(client)

    assert r.status_code == 502


def test_transcribe_admin_bypasses_entitlement(client):
    _override(
        _FakeUser(memberships=[], role_codes=["platform_admin"]),
        _FakeEntitlements(set()),
    )
    with patch(
        "app.modules.agent_platform.presentation.voice_router.transcribe_with_mai",
        new=AsyncMock(return_value={"text": "Admin"}),
    ):
        r = _transcribe(client)

    assert r.status_code == 200


# ---------------------------------------------------------------- live token


def test_voice_token_requires_auth(client):
    r = client.post("/api/v1/agent-platform/voice/token")
    assert r.status_code == 401


def test_voice_token_503_without_deepgram_key(client, monkeypatch):
    _override(
        _FakeUser(memberships=[{"companyId": "c1"}]),
        _FakeEntitlements({"c1"}),
    )
    monkeypatch.setenv("DEEPGRAM_API_KEY", "")
    r = client.post("/api/v1/agent-platform/voice/token")
    assert r.status_code == 503


def test_voice_token_502_on_provider_failure(client, monkeypatch):
    _override(
        _FakeUser(memberships=[{"companyId": "c1"}]),
        _FakeEntitlements({"c1"}),
    )
    monkeypatch.setenv("DEEPGRAM_API_KEY", "dk_test_x")

    class _Raises:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, *args, **kwargs):
            raise __import__("httpx").ConnectError("no network")

    with patch("httpx.AsyncClient", return_value=_Raises()):
        r = client.post("/api/v1/agent-platform/voice/token")

    assert r.status_code == 502


def test_voice_token_ok(client, monkeypatch):
    _override(
        _FakeUser(memberships=[{"companyId": "c1"}]),
        _FakeEntitlements({"c1"}),
    )
    monkeypatch.setenv("DEEPGRAM_API_KEY", "dk_test_x")

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"access_token": "dg-token-123", "expires_in": 60}

    class _FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, *args, **kwargs):
            return _FakeResponse()

    with patch("httpx.AsyncClient", return_value=_FakeClient()):
        r = client.post("/api/v1/agent-platform/voice/token")

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["access_token"] == "dg-token-123"
    assert body["expires_in"] == 60
