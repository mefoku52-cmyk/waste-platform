"""Unit tests for company services (basic)."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.companies.application.services import GetCompanyService
from app.shared.domain.exceptions import NotFoundDomainError


@pytest.mark.asyncio
async def test_get_company_not_found():
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=None)
    svc = GetCompanyService(repo)
    with pytest.raises(NotFoundDomainError):
        await svc.execute(uuid4())


@pytest.mark.asyncio
async def test_get_company_delegates():
    sentinel = object()
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=sentinel)
    svc = GetCompanyService(repo)

    from app.modules.companies.application import services as svc_mod

    original = svc_mod.to_company_dto
    svc_mod.to_company_dto = lambda x: x
    try:
        result = await svc.execute(uuid4())
        assert result is sentinel
    finally:
        svc_mod.to_company_dto = original
