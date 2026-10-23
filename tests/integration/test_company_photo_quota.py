"""Annual photo quota (10/company/calendar year) regression tests."""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from tests.integration._company_helpers import (
    clear_overrides,
    client_for,
    make_company,
    member_user,
)


@pytest.fixture(autouse=True)
def _clean_overrides():
    yield
    clear_overrides()


def _photo():
    return {"fileUrl": f"/api/v1/uploads/{uuid.uuid4().hex}.png"}


async def test_quota_meta_and_delete_does_not_reset_annual_quota():
    company_id = await make_company()
    admin = member_user(uuid.uuid4(), company_id, role="owner")
    async with client_for(admin) as client:
        ids = []
        for _ in range(10):
            r = await client.post(f"/api/v1/companies/{company_id}/photos", json=_photo())
            assert r.status_code == 200, r.text
            ids = [p["id"] for p in r.json()["items"]]

        quota = await client.get(f"/api/v1/companies/{company_id}/photos/quota")
        assert quota.status_code == 200, quota.text
        data = quota.json()
        assert data["uploadedThisYear"] == 10
        assert data["quotaPerYear"] == 10
        assert data["remainingThisYear"] == 0
        assert data["total"] == 10

        assert (
            await client.delete(f"/api/v1/companies/{company_id}/photos/{ids[0]}")
        ).status_code == 200

        over = await client.post(f"/api/v1/companies/{company_id}/photos", json=_photo())
        assert over.status_code == 422
        assert "ročný" in over.text.lower()


async def test_previous_year_photos_do_not_consume_current_quota():
    from app.modules.company_pages.infrastructure.models import CompanyPhotoModel
    from app.shared.infrastructure.db.session import async_session_factory

    company_id = await make_company()
    last_year = datetime(datetime.now().year - 1, 6, 1, 12, 0, 0)
    async with async_session_factory() as session:
        for i in range(3):
            session.add(
                CompanyPhotoModel(
                    id=str(uuid.uuid4()),
                    company_id=company_id,
                    file_url=f"/api/v1/uploads/old-{i}.png",
                    position=i,
                    is_primary=i == 0,
                    created_at=last_year,
                    updated_at=last_year,
                )
            )
        await session.commit()

    admin = member_user(uuid.uuid4(), company_id, role="owner")
    async with client_for(admin) as client:
        for _ in range(10):
            r = await client.post(f"/api/v1/companies/{company_id}/photos", json=_photo())
            assert r.status_code == 200, r.text

        quota = await client.get(f"/api/v1/companies/{company_id}/photos/quota")
        data = quota.json()
        assert data["uploadedThisYear"] == 10
        assert data["total"] == 13
        over = await client.post(f"/api/v1/companies/{company_id}/photos", json=_photo())
        assert over.status_code == 422
