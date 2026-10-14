"""AI draft SSE stream route tests — auth, AI tier gate, multi-company selection.

Regression: /listings/ai-draft/stream obchádzal AI tier gate (stream fungoval pre
každého prihláseného užívateľa), hoci frontend ai-draft-panel.tsx už 409 spracúva
ako ``ai_tier_required``. Teraz má rovnaký gate ako /listings/ai-draft.
"""

from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.companies.presentation.dependencies import get_entitlement_service
from app.shared.presentation.auth_dependencies import require_current_user


class _FakeUser:
    def __init__(self, memberships):
        self.id = str(uuid4())
        self.email = "test@example.com"
        self.isPlatformAdmin = False
        self.memberships = memberships


@pytest.fixture
def client():
    return TestClient(app)


def _override_user(memberships):
    app.dependency_overrides[require_current_user] = lambda: _FakeUser(memberships)


def _override_entitlement(ai_company_ids):
    """Fake entitlement: has_tier() vráti True iba pre company_id v množine."""

    class _FakeEntitlement:
        async def has_tier(self, company_id, minimum):
            return str(company_id) in ai_company_ids

    app.dependency_overrides[get_entitlement_service] = lambda: _FakeEntitlement()


@pytest.fixture(autouse=True)
def _cleanup_overrides():
    yield
    app.dependency_overrides.clear()


class _FakeDrafter:
    """ListingDrafter náhrada — stream() je async generátor udalostí SSE."""

    @staticmethod
    def is_provider_configured():
        return False

    async def stream(self, *, prompt, persona="bystry"):
        yield {"type": "draft", "title": "Oceľový šrot", "text": "Predám 5 ton"}


def _stream(client, **body):
    return client.stream(
        "POST",
        "/api/v1/listings/ai-draft/stream",
        json={"prompt": "Predám oceľový šrot", **body},
    )


def test_ai_draft_stream_requires_auth(client):
    r = client.post("/api/v1/listings/ai-draft/stream", json={"prompt": "test material"})
    assert r.status_code == 401


def test_ai_draft_stream_rejects_free_tier(client):
    _override_user([{"companyId": "c1"}])
    _override_entitlement(set())  # žiadna firma nemá AI

    r = client.post(
        "/api/v1/listings/ai-draft/stream",
        json={"prompt": "Predám oceľový šrot"},
    )
    assert r.status_code == 409


def test_ai_draft_stream_rejects_user_without_company(client):
    _override_user([])
    _override_entitlement(set())

    r = client.post(
        "/api/v1/listings/ai-draft/stream",
        json={"prompt": "Predám oceľový šrot"},
    )
    assert r.status_code == 409


def test_ai_draft_stream_ok_with_ai_tier(client):
    _override_user([{"companyId": "c1"}])
    _override_entitlement({"c1"})

    with (
        patch(
            "app.modules.listings.presentation.router.ListingDrafter",
            _FakeDrafter,
        ),
        _stream(client) as r,
    ):
        assert r.status_code == 200
        body = r.read().decode()
    assert "data: " in body
    assert "Oceľový šrot" in body


def test_ai_draft_stream_prefers_membership_with_ai_tier(client):
    """User má 2 firmy (c1 bez AI, c2 s AI). Stream sa spustí pre c2."""
    _override_user([{"companyId": "c1"}, {"companyId": "c2"}])
    _override_entitlement({"c2"})

    with (
        patch(
            "app.modules.listings.presentation.router.ListingDrafter",
            _FakeDrafter,
        ),
        _stream(client) as r,
    ):
        assert r.status_code == 200
        body = r.read().decode()
    assert "data: " in body


def test_ai_draft_stream_with_explicit_company_id(client):
    """company_id v tele prejde, ak má firma AI tier."""
    _override_user([{"companyId": "c9"}])
    _override_entitlement({"c9"})

    with (
        patch(
            "app.modules.listings.presentation.router.ListingDrafter",
            _FakeDrafter,
        ),
        _stream(client, company_id="c9") as r,
    ):
        assert r.status_code == 200
        body = r.read().decode()
    assert "data: " in body


def test_ai_draft_stream_explicit_company_without_tier_rejected(client):
    """company_id bez AI tieru → 409 (rovnako ako /ai-draft pre free firmu)."""
    _override_user([{"companyId": "c1"}, {"companyId": "c2"}])
    _override_entitlement({"c2"})  # c1 nemá AI

    r = client.post(
        "/api/v1/listings/ai-draft/stream",
        json={"prompt": "Predám šrot", "company_id": "c1"},
    )
    assert r.status_code == 409
