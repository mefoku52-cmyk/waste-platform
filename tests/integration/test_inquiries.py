"""Integration tests: inquiries API (auth, participant access, status, CRUD)."""

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


async def _make_inquiry(company_id, user, listing_id=None, status="open"):
    lid = listing_id or uuid.uuid4()
    async with client_for(user) as client:
        r = await client.post(
            "/api/v1/inquiries",
            json={
                "listingId": str(lid),
                "companyId": str(company_id),
                "message": "Dobry den, zaujem",
                "contactEmail": "buyer@example.com",
            },
        )
    return r, lid


async def test_create_requires_auth():
    company_id = await make_company()
    async with client_for(None) as client:
        r = await client.post(
            "/api/v1/inquiries",
            json={
                "listingId": str(uuid.uuid4()),
                "companyId": str(company_id),
                "message": "m",
                "contactEmail": "a@b.com",
            },
        )
    assert r.status_code == 401


async def test_create_requires_company_membership():
    company_id = await make_company()
    other = await make_company()
    user = member_user(uuid.uuid4(), other)
    async with client_for(user) as client:
        r = await client.post(
            "/api/v1/inquiries",
            json={
                "listingId": str(uuid.uuid4()),
                "companyId": str(company_id),
                "message": "m",
                "contactEmail": "a@b.com",
            },
        )
    assert r.status_code == 403


async def test_create_and_get_by_participant():
    company_id = await make_company()
    user = member_user(uuid.uuid4(), company_id)
    r, lid = await _make_inquiry(company_id, user)
    assert r.status_code == 201, r.text
    inq_id = r.json()["data"]["id"]
    assert r.json()["data"]["status"] == "open"

    # get by same user
    async with client_for(user) as client:
        g = await client.get(f"/api/v1/inquiries/{inq_id}")
    assert g.status_code == 200
    assert g.json()["data"]["id"] == inq_id


async def test_get_unknown_returns_404():
    company_id = await make_company()
    user = member_user(uuid.uuid4(), company_id)
    async with client_for(user) as client:
        g = await client.get(f"/api/v1/inquiries/{uuid.uuid4()}")
    assert g.status_code == 404


async def test_non_participant_cannot_get():
    c1 = await make_company()
    c2 = await make_company()
    u1 = member_user(uuid.uuid4(), c1)
    u2 = member_user(uuid.uuid4(), c2)
    r, _ = await _make_inquiry(c1, u1)
    inq_id = r.json()["data"]["id"]
    async with client_for(u2) as client:
        g = await client.get(f"/api/v1/inquiries/{inq_id}")
    assert g.status_code == 403


async def test_platform_admin_can_get_any():
    company_id = await make_company()
    user = member_user(uuid.uuid4(), company_id)
    r, _ = await _make_inquiry(company_id, user)
    inq_id = r.json()["data"]["id"]
    admin = platform_admin()
    async with client_for(admin) as client:
        g = await client.get(f"/api/v1/inquiries/{inq_id}")
    assert g.status_code == 200


async def test_list_sent_for_member():
    company_id = await make_company()
    user = member_user(uuid.uuid4(), company_id)
    await _make_inquiry(company_id, user)
    async with client_for(user) as client:
        r = await client.get("/api/v1/inquiries/sent")
    assert r.status_code == 200
    assert r.json()["meta"]["total"] >= 1


async def test_list_received_requires_ownership():
    company_id = await make_company()
    user = member_user(uuid.uuid4(), company_id)
    async with client_for(user) as client:
        r = await client.get("/api/v1/inquiries/received")
    assert r.status_code == 200


async def test_list_all_admin_only():
    company_id = await make_company()
    user = member_user(uuid.uuid4(), company_id)
    async with client_for(user) as client:
        r = await client.get("/api/v1/inquiries")
    assert r.status_code == 403
    admin = platform_admin()
    async with client_for(admin) as client:
        r2 = await client.get("/api/v1/inquiries")
    assert r2.status_code == 200


async def test_update_status_as_seller():
    # create inquiry for company c1 (buyer); seller is c2 owning listing
    c1 = await make_company()
    c2 = await make_company()
    buyer = member_user(uuid.uuid4(), c1)
    seller = member_user(uuid.uuid4(), c2, role="owner")
    listing_id = uuid.uuid4()
    # insert listing owned by c2 so seller_owns works? seller_owns checks listings table
    from datetime import datetime

    from app.modules.listings.infrastructure.models import ListingsModel
    from app.shared.infrastructure.db.session import async_session_factory

    now = datetime.now()
    async with async_session_factory() as session:
        session.add(
            ListingsModel(
                id=listing_id,
                company_id=__import__("uuid").UUID(str(c2)),
                title="Ponuka",
                material_type="plastic",
                quantity=10.0,
                unit="kg",
                condition="good",
                location="Bratislava",
                status="active",
                created_at=now,
                updated_at=now,
            )
        )
        await session.commit()
    r, _ = await _make_inquiry(c1, buyer, listing_id=listing_id)
    inq_id = r.json()["data"]["id"]

    async with client_for(seller) as client:
        p = await client.patch(f"/api/v1/inquiries/{inq_id}/status", json={"status": "answered"})
    assert p.status_code == 200, p.text
    assert p.json()["data"]["status"] == "answered"

    # buyer cannot change status
    async with client_for(buyer) as client:
        p2 = await client.patch(f"/api/v1/inquiries/{inq_id}/status", json={"status": "closed"})
    assert p2.status_code in (400, 403, 422)


async def test_delete_by_participant():
    company_id = await make_company()
    user = member_user(uuid.uuid4(), company_id)
    r, _ = await _make_inquiry(company_id, user)
    inq_id = r.json()["data"]["id"]
    async with client_for(user) as client:
        d = await client.delete(f"/api/v1/inquiries/{inq_id}")
    assert d.status_code == 204


async def test_delete_unknown_404():
    company_id = await make_company()
    user = member_user(uuid.uuid4(), company_id)
    async with client_for(user) as client:
        d = await client.delete(f"/api/v1/inquiries/{uuid.uuid4()}")
    assert d.status_code == 404
