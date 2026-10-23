"""Admin company overview/detail + admin authorization regression tests."""

from __future__ import annotations

import uuid

import pytest

from tests.integration._company_helpers import (
    clear_overrides,
    client_for,
    make_company,
    member_user,
    platform_admin,
)


@pytest.fixture(autouse=True)
def _clean_overrides():
    yield
    clear_overrides()


async def test_admin_companies_requires_auth():
    async with client_for(None) as client:
        r = await client.get("/api/v1/admin/companies")
    assert r.status_code == 401


async def test_admin_companies_rejects_non_admin():
    user = member_user(uuid.uuid4(), uuid.uuid4(), role="owner")
    async with client_for(user) as client:
        r = await client.get("/api/v1/admin/companies")
    assert r.status_code == 403


async def test_admin_companies_lists_and_detail():
    company_id = await make_company(
        legal_name="Admin Test s.r.o.",
        email="firma@example.com",
    )
    admin = platform_admin()
    async with client_for(admin) as client:
        r = await client.get("/api/v1/admin/companies", params={"q": "Admin Test"})
        assert r.status_code == 200, r.text
        items = r.json()["items"]
        assert any(item["id"] == company_id for item in items)

        d = await client.get(f"/api/v1/admin/companies/{company_id}")
        assert d.status_code == 200, d.text
        data = d.json()["data"]
        assert data["id"] == company_id
        assert data["legalName"] == "Admin Test s.r.o."
        assert data["email"] == "firma@example.com"
        assert data["counts"]["photos"] == 0


async def test_admin_company_detail_404():
    admin = platform_admin()
    async with client_for(admin) as client:
        r = await client.get(f"/api/v1/admin/companies/{uuid.uuid4()}")
    assert r.status_code == 404


async def test_admin_audit_endpoints_require_admin():
    user = member_user(uuid.uuid4(), uuid.uuid4(), role="owner")
    async with client_for(None) as client:
        assert (await client.get("/api/v1/admin/all")).status_code == 401
    async with client_for(user) as client:
        assert (await client.get("/api/v1/admin/all")).status_code == 403
        assert (await client.get("/api/v1/admin/stats")).status_code == 403
