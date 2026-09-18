"""Unit tests for InquiryService."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.inquiries.application.services import InquiryService
from app.modules.inquiries.domain.entities import InquiryEntity
from app.modules.inquiries.domain.enums import InquiryStatus
from app.shared.domain.exceptions import NotFoundDomainError, ValidationDomainError


def _inq(**over):
    base = {
        "id": uuid4(),
        "listing_id": uuid4(),
        "company_id": uuid4(),
        "message": "mam zaujem",
        "contact_email": "a@b.sk",
        "status": InquiryStatus.OPEN,
    }
    base.update(over)
    return InquiryEntity(**base)


@pytest.mark.asyncio
async def test_update_status_not_found():
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=None)
    svc = InquiryService(repo)
    with pytest.raises(NotFoundDomainError):
        await svc.update_status_as_seller(str(uuid4()), InquiryStatus.ANSWERED, [])


@pytest.mark.asyncio
async def test_update_status_not_seller():
    e = _inq()
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=e)
    repo.seller_owns_inquiry = AsyncMock(return_value=False)
    svc = InquiryService(repo)
    with pytest.raises(ValidationDomainError):
        await svc.update_status_as_seller(str(e.id), InquiryStatus.ANSWERED, ["other"])


@pytest.mark.asyncio
async def test_update_status_seller_success():
    e = _inq()
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=e)
    repo.seller_owns_inquiry = AsyncMock(return_value=True)
    repo.update = AsyncMock(return_value=e)
    svc = InquiryService(repo)
    result = await svc.update_status_as_seller(
        str(e.id), InquiryStatus.ANSWERED, [str(e.company_id)]
    )
    assert result.status == InquiryStatus.ANSWERED
    repo.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_calls_repo():
    repo = MagicMock()
    repo.create = AsyncMock(return_value=_inq())
    svc = InquiryService(repo)
    e = _inq()
    await svc.create(e)
    repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_not_found():
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=None)
    svc = InquiryService(repo)
    with pytest.raises(NotFoundDomainError):
        await svc.delete(str(uuid4()))
