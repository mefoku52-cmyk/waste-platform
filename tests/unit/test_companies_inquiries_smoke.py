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
