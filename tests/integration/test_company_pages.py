"""Integration tests: company_pages private + public API.

Covers: access control (auth/member/admin), tenant isolation, page CRUD,
publishing rules, slug validation/conflict, gallery limits and ownership,
public page visibility, and the stable public asset endpoint.
"""

from __future__ import annotations

import uuid

import pytest

from tests.integration._company_helpers import (
    clear_overrides,
    client_for,
    complete_page_payload,
    make_company,
    member_user,
    platform_admin,
)


@pytest.fixture(autouse=True)
def _clean_overrides():
    yield
    clear_overrides()


def _uniq(prefix="firma"):
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


# ─────────────────────────────────────────────────────────────
# Access control / isolation
# ─────────────────────────────────────────────────────────────


async def test_get_page_requires_auth():
    company_id = await make_company()
    async with client_for(None) as client:
        r = await client.get(f"/api/v1/companies/{company_id}/page")
    assert r.status_code == 401


async def test_non_member_cannot_read_page():
    company_id = await make_company()
    other = await make_company()
    user = member_user(uuid.uuid4(), other)
    async with client_for(user) as client:
        r = await client.get(f"/api/v1/companies/{company_id}/page")
    assert r.status_code == 403


async def test_member_reads_blank_page_when_missing():
    company_id = await make_company()
    user = member_user(uuid.uuid4(), company_id, role="viewer")
    async with client_for(user) as client:
        r = await client.get(f"/api/v1/companies/{company_id}/page")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["exists"] is False
    assert data["status"] == "draft"
    assert data["companyId"] == company_id
    # chýbajúce povinné polia sú vyznačené
    assert set(data["missingForPublish"]) >= {"displayName", "aboutShort", "contact"}


async def test_non_admin_member_cannot_edit():
    company_id = await make_company()
    user = member_user(uuid.uuid4(), company_id, role="viewer")
    async with client_for(user) as client:
        r = await client.put(f"/api/v1/companies/{company_id}/page", json=complete_page_payload())
    assert r.status_code == 403


async def test_platform_admin_can_read_any_company_page():
    company_id = await make_company()
    admin = platform_admin()
    async with client_for(admin) as client:
        r = await client.get(f"/api/v1/companies/{company_id}/page")
    assert r.status_code == 200


# ─────────────────────────────────────────────────────────────
# Page CRUD
# ─────────────────────────────────────────────────────────────


async def test_admin_upsert_creates_page_with_slug_from_display_name():
    company_id = await make_company()
    admin = member_user(uuid.uuid4(), company_id, role="owner")
    async with client_for(admin) as client:
        r = await client.put(
            f"/api/v1/companies/{company_id}/page",
            json=complete_page_payload(displayName="Zeleny Recycling"),
        )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["exists"] is True
    assert data["slug"].startswith("zeleny-recycling")
    assert data["status"] == "draft"
    assert data["missingForPublish"] == []


async def test_upsert_is_idempotent_one_page_per_company():
    company_id = await make_company()
    admin = member_user(uuid.uuid4(), company_id, role="owner")
    async with client_for(admin) as client:
        await client.put(f"/api/v1/companies/{company_id}/page", json=complete_page_payload())
        r2 = await client.put(
            f"/api/v1/companies/{company_id}/page",
            json=complete_page_payload(aboutShort="Novy popis firmy."),
        )
        listing = await client.get(f"/api/v1/companies/{company_id}/page")
    assert r2.status_code == 200
    assert listing.json()["data"]["aboutShort"] == "Novy popis firmy."


async def test_slug_conflict_returns_409():
    c1 = await make_company()
    c2 = await make_company()
    shared = _uniq("shared")
    a1 = member_user(uuid.uuid4(), c1, role="owner")
    a2 = member_user(uuid.uuid4(), c2, role="owner")
    async with client_for(a1) as client:
        r1 = await client.put(
            f"/api/v1/companies/{c1}/page", json=complete_page_payload(slug=shared)
        )
    assert r1.status_code == 200
    async with client_for(a2) as client:
        r2 = await client.put(
            f"/api/v1/companies/{c2}/page", json=complete_page_payload(slug=shared)
        )
    assert r2.status_code == 409


async def test_invalid_slug_returns_422():
    company_id = await make_company()
    admin = member_user(uuid.uuid4(), company_id, role="owner")
    async with client_for(admin) as client:
        r = await client.put(
            f"/api/v1/companies/{company_id}/page",
            json=complete_page_payload(slug="a"),
        )
    assert r.status_code == 422


async def test_slug_available_endpoint():
    c1 = await make_company()
    c2 = await make_company()
    taken = _uniq("taken")
    admin1 = member_user(uuid.uuid4(), c1, role="owner")
    admin2 = member_user(uuid.uuid4(), c2, role="owner")
    async with client_for(admin1) as client:
        await client.put(f"/api/v1/companies/{c1}/page", json=complete_page_payload(slug=taken))
    async with client_for(admin2) as client:
        r = await client.get(f"/api/v1/companies/{c2}/page/slug-available", params={"slug": taken})
        r2 = await client.get(
            f"/api/v1/companies/{c2}/page/slug-available",
            params={"slug": _uniq("volne")},
        )
    assert r.status_code == 200
    assert r.json()["available"] is False
    assert r.json()["reason"] == "taken"
    assert r2.json()["available"] is True


# ─────────────────────────────────────────────────────────────
# Publish / unpublish
# ─────────────────────────────────────────────────────────────


async def test_publish_requires_verified_company():
    company_id = await make_company(status="draft")
    admin = member_user(uuid.uuid4(), company_id, role="owner")
    async with client_for(admin) as client:
        await client.put(f"/api/v1/companies/{company_id}/page", json=complete_page_payload())
        r = await client.post(f"/api/v1/companies/{company_id}/page/publish")
    assert r.status_code == 422


async def test_publish_requires_mandatory_fields():
    company_id = await make_company(status="verified")
    admin = member_user(uuid.uuid4(), company_id, role="owner")
    async with client_for(admin) as client:
        await client.put(
            f"/api/v1/companies/{company_id}/page",
            json={"displayName": "Bez kontaktu"},  # chýba aboutShort + kontakt
        )
        r = await client.post(f"/api/v1/companies/{company_id}/page/publish")
    assert r.status_code == 422
    assert "chýbajú" in r.json()["detail"].lower()


async def test_publish_then_public_visible_then_unpublish_hides():
    company_id = await make_company(status="verified")
    admin = member_user(uuid.uuid4(), company_id, role="owner")
    async with client_for(admin) as client:
        await client.put(f"/api/v1/companies/{company_id}/page", json=complete_page_payload())
        pub = await client.post(f"/api/v1/companies/{company_id}/page/publish")
        assert pub.status_code == 200, pub.text
        slug = pub.json()["data"]["slug"]
        assert pub.json()["data"]["status"] == "published"

    # verejný endpoint bez auth
    async with client_for(None) as client:
        public = await client.get(f"/api/v1/public/company-pages/{slug}")
        assert public.status_code == 200
        body = public.json()
        assert body["displayName"] == "Eko Odpad s.r.o."
        assert body["company"]["verified"] is True
        assert "secret" not in body  # sanity: žiadne interné polia

    # odpublikovanie → 404 verejne
    async with client_for(admin) as client:
        unpub = await client.post(f"/api/v1/companies/{company_id}/page/unpublish")
        assert unpub.status_code == 200
        assert unpub.json()["data"]["status"] == "draft"
    async with client_for(None) as client:
        hidden = await client.get(f"/api/v1/public/company-pages/{slug}")
    assert hidden.status_code == 404


async def test_public_page_not_found_for_unknown_slug():
    async with client_for(None) as client:
        r = await client.get("/api/v1/public/company-pages/neexistuje-xyz")
    assert r.status_code == 404


async def test_public_page_404_for_draft_only():
    company_id = await make_company(status="verified")
    admin = member_user(uuid.uuid4(), company_id, role="owner")
    async with client_for(admin) as client:
        r = await client.put(
            f"/api/v1/companies/{company_id}/page",
            json=complete_page_payload(slug=_uniq("draft")),
        )
        slug = r.json()["data"]["slug"]
    async with client_for(None) as client:
        pub = await client.get(f"/api/v1/public/company-pages/{slug}")
    assert pub.status_code == 404


# ─────────────────────────────────────────────────────────────
# Gallery
# ─────────────────────────────────────────────────────────────


def _photo(fid=None):
    return {"fileUrl": f"/api/v1/uploads/{fid or uuid.uuid4().hex}.png"}


async def test_gallery_add_list_limits_and_ownership():
    company_id = await make_company()
    other = await make_company()
    admin = member_user(uuid.uuid4(), company_id, role="owner")
    outsider = member_user(uuid.uuid4(), other, role="viewer")

    async with client_for(admin) as client:
        # 10 fotiek OK
        for _ in range(10):
            r = await client.post(f"/api/v1/companies/{company_id}/photos", json=_photo())
            assert r.status_code == 200, r.text
        assert len(r.json()["items"]) == 10
        # 11. fotka → limit
        over = await client.post(f"/api/v1/companies/{company_id}/photos", json=_photo())
        assert over.status_code == 422

    # člen inej firmy nevidí fotky
    async with client_for(outsider) as client:
        r = await client.get(f"/api/v1/companies/{company_id}/photos")
    assert r.status_code == 403


async def test_gallery_delete_and_primary_and_reorder():
    company_id = await make_company()
    admin = member_user(uuid.uuid4(), company_id, role="owner")
    async with client_for(admin) as client:
        r1 = await client.post(f"/api/v1/companies/{company_id}/photos", json=_photo())
        ids = [p["id"] for p in r1.json()["items"]]
        r2 = await client.post(f"/api/v1/companies/{company_id}/photos", json=_photo())
        ids = [p["id"] for p in r2.json()["items"]]
        assert r2.json()["items"][0]["isPrimary"] is True  # prvá je primary

        # nastav druhú ako primary
        prim = await client.post(f"/api/v1/companies/{company_id}/photos/{ids[1]}/primary")
        assert prim.status_code == 200
        assert {p["id"]: p["isPrimary"] for p in prim.json()["items"]}[ids[1]] is True

        # reorder (obrátené poradie)
        reorder = await client.put(
            f"/api/v1/companies/{company_id}/photos/order",
            json={"orderedIds": list(reversed(ids))},
        )
        assert reorder.status_code == 200
        assert [p["id"] for p in reorder.json()["items"]] == list(reversed(ids))

        # zmazanie primary → nová primary z ostatných
        dele = await client.delete(f"/api/v1/companies/{company_id}/photos/{ids[1]}")
        assert dele.status_code == 200
        assert len(dele.json()["items"]) == 1
        assert dele.json()["items"][0]["isPrimary"] is True


async def test_gallery_requires_admin():
    company_id = await make_company()
    viewer = member_user(uuid.uuid4(), company_id, role="viewer")
    async with client_for(viewer) as client:
        r = await client.post(f"/api/v1/companies/{company_id}/photos", json=_photo())
    assert r.status_code == 403


# ─────────────────────────────────────────────────────────────
# Public asset endpoint
# ─────────────────────────────────────────────────────────────


async def test_public_asset_serves_only_published_company_files(tmp_path, monkeypatch):
    import app.modules.company_pages.presentation.public_router as pr

    monkeypatch.setattr(pr, "UPLOAD_ROOT", tmp_path)

    fid = uuid.uuid4().hex + ".png"
    (tmp_path / fid).write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 32)

    company_id = await make_company(status="verified")
    admin = member_user(uuid.uuid4(), company_id, role="owner")
    async with client_for(admin) as client:
        await client.put(f"/api/v1/companies/{company_id}/page", json=complete_page_payload())
        await client.post(
            f"/api/v1/companies/{company_id}/photos",
            json={"fileUrl": f"/api/v1/uploads/{fid}"},
        )
        pub = await client.post(f"/api/v1/companies/{company_id}/page/publish")
        slug = pub.json()["data"]["slug"]

    async with client_for(None) as client:
        ok = await client.get(f"/api/v1/public/company-pages/{slug}/assets/{fid}")
        assert ok.status_code == 200, ok.text
        assert ok.content.startswith(b"\x89PNG")
        # cudzí súbor (nie je v galérii/logu/ponuke) → 404
        other_fid = uuid.uuid4().hex + ".png"
        (tmp_path / other_fid).write_bytes(b"\x89PNG\r\n\x1a\n")
        miss = await client.get(f"/api/v1/public/company-pages/{slug}/assets/{other_fid}")
        assert miss.status_code == 404
        # neplatný file_id → 400
        bad = await client.get(f"/api/v1/public/company-pages/{slug}/assets/not-a-file")
        assert bad.status_code == 400


# ─────────────────────────────────────────────────────────────
# Public sitemap listing (SEO)
# ─────────────────────────────────────────────────────────────


async def test_public_sitemap_lists_only_published_slugs():
    draft_company = await make_company(status="verified")
    pub_company = await make_company(status="verified")
    draft_admin = member_user(uuid.uuid4(), draft_company, role="owner")
    pub_admin = member_user(uuid.uuid4(), pub_company, role="owner")
    draft_slug = _uniq("koncept")
    pub_slug = _uniq("zverejnena")

    async with client_for(draft_admin) as client:
        await client.put(
            f"/api/v1/companies/{draft_company}/page",
            json=complete_page_payload(slug=draft_slug),
        )
    async with client_for(pub_admin) as client:
        await client.put(
            f"/api/v1/companies/{pub_company}/page",
            json=complete_page_payload(slug=pub_slug),
        )
        await client.post(f"/api/v1/companies/{pub_company}/page/publish")

    async with client_for(None) as client:
        r = await client.get("/api/v1/public/company-pages")
    assert r.status_code == 200, r.text
    slugs = [item["slug"] for item in r.json()["items"]]
    assert pub_slug in slugs
    assert draft_slug not in slugs
    assert r.json()["meta"]["total"] == len(slugs)
