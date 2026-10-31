"""Companies & inquiries routers — TestClient smoke tests with dependency overrides."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_companies_list_without_auth_401(client):
    r = client.get("/api/v1/companies")
    assert r.status_code == 401


def test_companies_get_without_auth_401(client):
    r = client.get("/api/v1/companies/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 401


def test_inquiries_list_without_auth_401(client):
    r = client.get("/api/v1/inquiries")
    assert r.status_code == 401


def test_inquiries_received_without_auth_401(client):
    r = client.get("/api/v1/inquiries/received")
    assert r.status_code == 401


def test_inquiries_sent_without_auth_401(client):
    r = client.get("/api/v1/inquiries/sent")
    assert r.status_code == 401


def test_openapi_has_companies_paths():
    schema = app.openapi()
    assert "/api/v1/companies" in schema["paths"]
    assert "/api/v1/companies/{company_id}" in schema["paths"]


def test_openapi_has_inquiries_paths():
    schema = app.openapi()
    assert "/api/v1/inquiries" in schema["paths"]
    assert "/api/v1/inquiries/{id}" in schema["paths"]


def test_companies_list_with_overridden_deps_returns_200(client):
    from app.modules.companies.presentation.dependencies import get_list_companies_service
    from app.shared.presentation.auth_dependencies import require_current_user

    class _FakeUser:
        def __init__(self):
            self.user = type("U", (), {"id": "00000000-0000-0000-0000-000000000001"})()
            self.memberships = []

    class _StubService:
        async def execute(self, **kwargs):
            return ([], 0)

    app.dependency_overrides[require_current_user] = lambda: _FakeUser()
    app.dependency_overrides[get_list_companies_service] = lambda: _StubService()
    try:
        r = client.get("/api/v1/companies")
        assert r.status_code == 200
        assert r.json()["meta"]["total"] == 0
    finally:
        app.dependency_overrides.clear()


def test_inquiries_received_with_overridden_deps_returns_200(client):
    from app.modules.inquiries.presentation.dependencies import get_inquiries_service
    from app.shared.presentation.auth_dependencies import require_current_user

    class _FakeUser:
        def __init__(self):
            self.memberships = []

    class _StubService:
        async def list_received(self, page, pageSize, seller_company_ids=None):
            return []

        async def count_received(self, seller_company_ids=None):
            return 0

    app.dependency_overrides[require_current_user] = lambda: _FakeUser()
    app.dependency_overrides[get_inquiries_service] = lambda: _StubService()
    try:
        r = client.get("/api/v1/inquiries/received")
        assert r.status_code == 200
        assert r.json()["meta"]["total"] == 0
    finally:
        app.dependency_overrides.clear()


def test_company_directory_redacts_sensitive_fields_and_does_not_widen_without_flag():
    from datetime import UTC, datetime
    from types import SimpleNamespace
    from uuid import uuid4

    from app.modules.companies.presentation.dependencies import get_list_companies_service
    from app.shared.presentation.auth_dependencies import require_current_user

    company_id = uuid4()
    reviewer_id = uuid4()
    created = datetime.now(UTC)
    item = SimpleNamespace(
        id=company_id, status="verified", legal_name="Public Co", trading_name=None,
        registration_number="12345678", tax_identifier="tax-secret", vat_identifier="vat-secret",
        subscription_tier="free", company_type="seller", email="private@example.test",
        phone="+421900000000", website_url="https://example.test", logo_url=None,
        country_code="SK", address_line_1="Private Street 1", address_line_2=None,
        city="Bratislava", postal_code="81101", latitude=48.1, longitude=17.1,
        seller_capability=True, buyer_capability=False, logistics_capability=False,
        verification_submitted_at=created, verification_reviewed_at=created,
        verification_reviewed_by_user_id=reviewer_id, verified_at=created,
        verified_by_user_id=reviewer_id, rejected_at=None, rejected_by_user_id=None,
        created_at=created, created_by_user_id=reviewer_id, updated_at=created,
        updated_by_user_id=reviewer_id,
    )
    calls = []

    class User:
        memberships = [{"companyId": company_id}]
        roleCodes = []

    class Service:
        async def execute(self, **kwargs):
            calls.append(kwargs)
            return [item], 1

    app.dependency_overrides[require_current_user] = lambda: User()
    app.dependency_overrides[get_list_companies_service] = lambda: Service()
    try:
        with TestClient(app) as client:
            directory_response = client.get("/api/v1/companies?directory=true")
            assert directory_response.status_code == 200
            public_item = directory_response.json()["items"][0]
            assert public_item["legalName"] == "Public Co"
            assert not ({"taxIdentifier", "vatIdentifier", "email", "phone", "websiteUrl",
                         "addressLine1", "addressLine2", "postalCode", "latitude", "longitude",
                         "verificationReviewedByUserId", "verifiedByUserId", "createdByUserId",
                         "updatedByUserId"} & public_item.keys())
            assert calls[-1]["company_ids"] is None

            member_response = client.get("/api/v1/companies")
            assert member_response.status_code == 200
            member_item = member_response.json()["items"][0]
            assert member_item["taxIdentifier"] == "tax-secret"
            assert member_item["email"] == "private@example.test"
            assert calls[-1]["company_ids"] == [company_id]
    finally:
        app.dependency_overrides.clear()


def test_company_directory_openapi_declares_limited_and_full_response_shapes():
    from app.modules.companies.presentation.schemas import CompanyDirectoryData

    schema = app.openapi()
    item_schema = schema["components"]["schemas"]["PaginatedCompaniesResponse"]["properties"]["items"]["items"]
    refs = {variant.get("$ref", "").rsplit("/", 1)[-1] for variant in item_schema["anyOf"]}
    assert refs == {"CompanyData", CompanyDirectoryData.__name__}
