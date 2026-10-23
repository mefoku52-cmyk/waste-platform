"""AI draft route tests — auth, AI tier gate, multi-company selection."""

from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.companies.presentation.dependencies import get_entitlement_service
from app.shared.presentation.auth_dependencies import require_current_user


class _FakeUser:
    def __init__(self, memberships, role_codes=None):
        self.id = str(uuid4())
        self.email = "test@example.com"
        self.isPlatformAdmin = False
        self.memberships = memberships
        self.roleCodes = role_codes or []


@pytest.fixture
def client():
    return TestClient(app)


def _override_user(memberships, role_codes=None):
    app.dependency_overrides[require_current_user] = lambda: _FakeUser(memberships, role_codes)


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


def test_ai_draft_requires_auth(client):
    r = client.post("/api/v1/listings/ai-draft", json={"prompt": "test material"})
    assert r.status_code == 401


def test_ai_draft_rejects_free_tier(client):
    _override_user([{"companyId": "c1"}])
    _override_entitlement(set())  # žiadna firma nemá AI

    r = client.post(
        "/api/v1/listings/ai-draft",
        json={"prompt": "Predám oceľový šrot"},
    )
    assert r.status_code == 409


def test_ai_draft_prefers_membership_with_ai_tier(client):
    """User má 2 firmy (c1 bez AI, c2 s AI). Draft sa musí vygenerovať pre c2."""
    _override_user([{"companyId": "c1"}, {"companyId": "c2"}])
    _override_entitlement({"c2"})

    seen_company = {}

    class _FakeDrafter:
        @staticmethod
        def is_provider_configured():
            return False

        async def draft(self, *, prompt, persona="bystry"):
            class _D:
                title = "t"
                description = "d"
                materialType = None
                quantity = None
                unit = None
                location = None
                condition = None
                currency = "EUR"
                price = None

            seen_company["called"] = True
            return _D()

    with patch("app.modules.listings.application.listing_drafter.ListingDrafter", _FakeDrafter):
        r = client.post(
            "/api/v1/listings/ai-draft",
            json={"prompt": "Predám oceľový šrot"},
        )

    assert r.status_code == 200, r.text
    assert seen_company.get("called") is True
    body = r.json()
    assert body["provider"] == "fallback"


def test_ai_draft_ok_with_ai_tier(client):
    _override_user([{"companyId": "c1"}])
    _override_entitlement({"c1"})

    class _FakeDrafter:
        @staticmethod
        def is_provider_configured():
            return False

        async def draft(self, *, prompt, persona="bystry"):
            class _D:
                title = "Oceľový šrot"
                description = "Predám"
                materialType = "ocel"
                quantity = 5.0
                unit = "t"
                location = "Bratislava"
                condition = "pouzite"
                currency = "EUR"
                price = None

            return _D()

    with patch("app.modules.listings.application.listing_drafter.ListingDrafter", _FakeDrafter):
        r = client.post(
            "/api/v1/listings/ai-draft",
            json={"prompt": "Predám 5 ton oceľového šrotu"},
        )

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["provider"] == "fallback"
    assert body["data"]["title"] == "Oceľový šrot"


def test_ai_draft_persona_forwarded(client):
    """Persona v request body sa preposle do draftera."""
    _override_user([{"companyId": "c1"}])
    _override_entitlement({"c1"})

    seen = {}

    class _FakeDrafter:
        @staticmethod
        def is_provider_configured():
            return False

        async def draft(self, *, prompt, persona="bystry"):
            seen["persona"] = persona

            class _D:
                title = "x"
                description = "y"
                materialType = None
                quantity = None
                unit = None
                location = None
                condition = None
                currency = "EUR"
                price = None

            return _D()

    with patch("app.modules.listings.application.listing_drafter.ListingDrafter", _FakeDrafter):
        r = client.post(
            "/api/v1/listings/ai-draft",
            json={"prompt": "Predám šrot", "persona": "drzy"},
        )

    assert r.status_code == 200, r.text
    assert seen.get("persona") == "drzy"


class _FakeDrafter:
    def __init__(self, called=None):
        self._called = called if called is not None else {}

    @staticmethod
    def is_provider_configured():
        return False

    async def draft(self, *, prompt, persona="bystry"):
        self._called["draft"] = True

        class _D:
            title = "t"
            description = "d"
            materialType = None
            quantity = None
            unit = None
            location = None
            condition = None
            currency = "EUR"
            price = None

        return _D()


def test_ai_draft_explicit_company_rejects_non_member(client):
    """Explicitné companyId mimo členstva → 403 aj pri AI tier; drafter sa nespustí."""
    member_id = str(uuid4())
    other_id = str(uuid4())
    _override_user([{"companyId": member_id}])
    _override_entitlement({other_id})

    called = {}

    with patch(
        "app.modules.listings.application.listing_drafter.ListingDrafter",
        lambda: _FakeDrafter(called),
    ):
        r = client.post(
            "/api/v1/listings/ai-draft",
            json={"prompt": "Predám oceľový šrot", "companyId": other_id},
        )

    assert r.status_code == 403, r.text
    assert "draft" not in called


def test_ai_draft_explicit_company_allows_member(client):
    """Explicitné companyId člena firmy s AI tier → draft sa vygeneruje."""
    member_id = str(uuid4())
    _override_user([{"companyId": member_id}])
    _override_entitlement({member_id})

    called = {}

    with patch(
        "app.modules.listings.application.listing_drafter.ListingDrafter",
        lambda: _FakeDrafter(called),
    ):
        r = client.post(
            "/api/v1/listings/ai-draft",
            json={"prompt": "Predám oceľový šrot", "companyId": member_id},
        )

    assert r.status_code == 200, r.text
    assert called.get("draft") is True


def test_ai_draft_explicit_company_allows_platform_admin(client):
    """Platform admin obchádza členstvo (require_company_member bypass)."""
    other_id = str(uuid4())
    _override_user([], role_codes=["platform_admin"])
    _override_entitlement({other_id})

    called = {}

    with patch(
        "app.modules.listings.application.listing_drafter.ListingDrafter",
        lambda: _FakeDrafter(called),
    ):
        r = client.post(
            "/api/v1/listings/ai-draft",
            json={"prompt": "Predám oceľový šrot", "companyId": other_id},
        )

    assert r.status_code == 200, r.text
    assert called.get("draft") is True
