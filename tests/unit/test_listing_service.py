"""Unit tests for ListingsService."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.listings.application.services import ListingsService
from app.modules.listings.domain.entities import ListingsEntity
from app.modules.listings.domain.enums import ListingsStatus
from app.shared.domain.exceptions import (
    ForbiddenDomainError,
    NotFoundDomainError,
    ValidationDomainError,
)


def _listing(**over):
    base = {
        "id": uuid4(),
        "title": "Test",
        "material_type": "PET",
        "quantity": 10.0,
        "unit": "kg",
        "condition": "new",
        "location": "BA",
        "company_id": str(uuid4()),
        "status": ListingsStatus.DRAFT,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    base.update(over)
    return ListingsEntity(**base)


@pytest.mark.asyncio
async def test_publish_not_found():
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=None)
    svc = ListingsService(repo)
    with pytest.raises(NotFoundDomainError):
        await svc.publish(str(uuid4()))


@pytest.mark.asyncio
async def test_publish_requires_verified_company():
    lst = _listing()
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=lst)
    repo.get_company_status = AsyncMock(return_value="draft")
    svc = ListingsService(repo)
    with pytest.raises(ValidationDomainError):
        await svc.publish(str(lst.id))


@pytest.mark.asyncio
async def test_publish_success():
    lst = _listing()
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=lst)
    repo.get_company_status = AsyncMock(return_value="verified")
    repo.update = AsyncMock(return_value=lst)
    svc = ListingsService(repo)
    result = await svc.publish(str(lst.id))
    assert result.status == ListingsStatus.PUBLISHED
    repo.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_stats_not_found():
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=None)
    svc = ListingsService(repo)
    with pytest.raises(NotFoundDomainError):
        await svc.get_stats(str(uuid4()))


@pytest.mark.asyncio
async def test_get_stats_wrong_owner():
    lst = _listing()
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=lst)
    svc = ListingsService(repo)
    with pytest.raises(ForbiddenDomainError):
        await svc.get_stats(str(lst.id), owner_company_ids=["other-company"])


@pytest.mark.asyncio
async def test_get_stats_rejects_user_without_company_memberships():
    lst = _listing()
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=lst)
    repo.get_listing_stats = AsyncMock(return_value={"views": 7, "unique_viewers": 3})
    svc = ListingsService(repo)

    with pytest.raises(ForbiddenDomainError):
        await svc.get_stats(str(lst.id), owner_company_ids=[])

    repo.get_listing_stats.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_stats_owner_success():
    lst = _listing()
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=lst)
    repo.get_listing_stats = AsyncMock(return_value={"views": 7, "unique_viewers": 3})
    svc = ListingsService(repo)
    stats = await svc.get_stats(str(lst.id), owner_company_ids=[lst.company_id])
    assert stats == {"views": 7, "uniqueViewers": 3}


@pytest.mark.asyncio
async def test_record_view_not_found():
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=None)
    svc = ListingsService(repo)
    with pytest.raises(NotFoundDomainError):
        await svc.record_view(str(uuid4()), uuid4())


@pytest.mark.asyncio
async def test_record_view_success():
    lst = _listing()
    uid = uuid4()
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=lst)
    repo.record_view = AsyncMock(return_value=None)
    svc = ListingsService(repo)
    await svc.record_view(str(lst.id), uid)
    repo.record_view.assert_awaited_once()
