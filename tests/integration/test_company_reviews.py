"""Integration tests: company_reviews.

Covers eligibility (member / no-inquiry denied, completed inquiry allowed),
duplicates, moderation (platform-admin only), public visibility of approved
reviews + aggregate rating, and rating validation.
"""

from __future__ import annotations

import uuid

import pytest

from tests.integration._company_helpers import (
    clear_overrides,
    client_for,
    complete_page_payload,
    make_company,
    make_inquiry,
    member_user,
    platform_admin,
)


@pytest.fixture(autouse=True)
def _clean_overrides():
    yield
    clear_overrides()


async def test_review_requires_auth():
    company_id = await make_company()
    async with client_for(None) as client:
        r = await client.post(f"/api/v1/companies/{company_id}/reviews", json={"rating": 5})
    assert r.status_code == 401


async def test_member_cannot_review_own_company():
    company_id = await make_company()
    member = member_user(uuid.uuid4(), company_id, role="owner")
    async with client_for(member) as client:
        r = await client.post(f"/api/v1/companies/{company_id}/reviews", json={"rating": 5})
    assert r.status_code == 403


async def test_review_requires_completed_inquiry():
    company_id = await make_company()
    buyer = member_user(uuid.uuid4(), await make_company(), role="viewer")
    # buyer is member of ANOTHER company → not member of target
    async with client_for(buyer) as client:
        r = await client.post(
            f"/api/v1/companies/{company_id}/reviews", json={"rating": 4, "body": "ok"}
        )
    assert r.status_code == 403
    assert "dopyte" in r.json()["detail"].lower()


async def test_review_allowed_after_completed_inquiry_and_pending():
    company_id = await make_company()
    other = await make_company()
    buyer_id = uuid.uuid4()
    buyer = member_user(buyer_id, other, role="viewer")
    await make_inquiry(company_id, buyer_id, status="answered")
    async with client_for(buyer) as client:
        r = await client.post(
            f"/api/v1/companies/{company_id}/reviews",
            json={"rating": 5, "title": "Super", "body": "Rychle a korektne."},
        )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["status"] == "pending"
    assert data["rating"] == 5


async def test_open_inquiry_not_enough():
    company_id = await make_company()
    other = await make_company()
    buyer_id = uuid.uuid4()
    buyer = member_user(buyer_id, other, role="viewer")
    await make_inquiry(company_id, buyer_id, status="open")
    async with client_for(buyer) as client:
        r = await client.post(f"/api/v1/companies/{company_id}/reviews", json={"rating": 3})
    assert r.status_code == 403


async def test_duplicate_review_conflict():
    company_id = await make_company()
    other = await make_company()
    buyer_id = uuid.uuid4()
    buyer = member_user(buyer_id, other, role="viewer")
    await make_inquiry(company_id, buyer_id, status="closed")
    async with client_for(buyer) as client:
        r1 = await client.post(f"/api/v1/companies/{company_id}/reviews", json={"rating": 5})
        r2 = await client.post(f"/api/v1/companies/{company_id}/reviews", json={"rating": 1})
    assert r1.status_code == 201
    assert r2.status_code == 409


async def test_rating_validation():
    company_id = await make_company()
    other = await make_company()
    buyer_id = uuid.uuid4()
    buyer = member_user(buyer_id, other, role="viewer")
    await make_inquiry(company_id, buyer_id, status="answered")
    async with client_for(buyer) as client:
        r0 = await client.post(f"/api/v1/companies/{company_id}/reviews", json={"rating": 0})
        r6 = await client.post(f"/api/v1/companies/{company_id}/reviews", json={"rating": 6})
    assert r0.status_code == 422
    assert r6.status_code == 422


async def test_moderation_requires_platform_admin_then_public_visibility():
    company_id = await make_company(status="verified")
    owner = member_user(uuid.uuid4(), company_id, role="owner")
    other = await make_company()
    buyer_id = uuid.uuid4()
    buyer = member_user(buyer_id, other, role="viewer")
    await make_inquiry(company_id, buyer_id, status="answered")

    # recenzia
    async with client_for(buyer) as client:
        r = await client.post(
            f"/api/v1/companies/{company_id}/reviews",
            json={"rating": 4, "title": "Dobre", "body": "Odporucam."},
        )
    review_id = r.json()["data"]["id"]

    # owner publikuje stránku
    async with client_for(owner) as client:
        await client.put(f"/api/v1/companies/{company_id}/page", json=complete_page_payload())
        pub = await client.post(f"/api/v1/companies/{company_id}/page/publish")
        slug = pub.json()["data"]["slug"]

    # pending recenzia NIE je verejná
    async with client_for(None) as client:
        public = await client.get(f"/api/v1/public/company-pages/{slug}")
        assert public.json()["reviews"] == []
        assert public.json()["ratingCount"] == 0

    # member firmy (nie platform admin) nemôže moderovať
    async with client_for(owner) as client:
        denied = await client.patch(
            f"/api/v1/companies/{company_id}/reviews/{review_id}/moderate",
            json={"status": "approved"},
        )
    assert denied.status_code == 403

    # platform admin schváli
    admin = platform_admin()
    async with client_for(admin) as client:
        ok = await client.patch(
            f"/api/v1/companies/{company_id}/reviews/{review_id}/moderate",
            json={"status": "approved"},
        )
    assert ok.status_code == 200, ok.text
    assert ok.json()["data"]["status"] == "approved"

    # teraz verejne viditeľná + agregát
    async with client_for(None) as client:
        public = await client.get(f"/api/v1/public/company-pages/{slug}")
    body = public.json()
    assert len(body["reviews"]) == 1
    assert body["reviews"][0]["rating"] == 4
    assert body["ratingCount"] == 1
    assert body["ratingAverage"] == 4.0


async def test_owner_sees_all_states_nonmember_sees_only_approved():
    company_id = await make_company()
    owner = member_user(uuid.uuid4(), company_id, role="owner")
    other = await make_company()
    buyer_id = uuid.uuid4()
    buyer = member_user(buyer_id, other, role="viewer")
    await make_inquiry(company_id, buyer_id, status="answered")
    async with client_for(buyer) as client:
        await client.post(f"/api/v1/companies/{company_id}/reviews", json={"rating": 3})

    async with client_for(owner) as client:
        allr = await client.get(f"/api/v1/companies/{company_id}/reviews")
    assert allr.json()["meta"]["total"] == 1
    assert allr.json()["items"][0]["status"] == "pending"

    async with client_for(None) as client:
        # bez auth → 401 (nie verejný endpoint; verejné sú len cez /public/...)
        r = await client.get(f"/api/v1/companies/{company_id}/reviews")
    assert r.status_code == 401


async def test_author_can_read_own_review_via_mine():
    """Autor recenzie je NIE člen firmy — /mine musí byť dostupné oprávnenému autorovi.

    Regresný test: predtým /mine vyžadoval členstvo, takže skutočný autor (nečlen)
    dostal 403 a nemohol si predvyplniť/ovoriť svoju recenziu.
    """
    company_id = await make_company()
    other = await make_company()
    buyer_id = uuid.uuid4()
    buyer = member_user(buyer_id, other, role="viewer")
    await make_inquiry(company_id, buyer_id, status="answered")

    # najprv bez recenzie → hasReview False
    async with client_for(buyer) as client:
        empty = await client.get(f"/api/v1/companies/{company_id}/reviews/mine")
    assert empty.status_code == 200, empty.text
    assert empty.json()["data"]["eligibility"]["hasReview"] is False

    async with client_for(buyer) as client:
        await client.post(f"/api/v1/companies/{company_id}/reviews", json={"rating": 4})
        mine = await client.get(f"/api/v1/companies/{company_id}/reviews/mine")
    assert mine.status_code == 200, mine.text
    assert mine.json()["data"]["eligibility"]["hasReview"] is True


async def test_mine_requires_auth():
    company_id = await make_company()
    async with client_for(None) as client:
        r = await client.get(f"/api/v1/companies/{company_id}/reviews/mine")
    assert r.status_code == 401
