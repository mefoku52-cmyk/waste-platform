"""Smoke tests for listings and companies services."""

import pytest

from app.modules.companies.application.services import CreateCompanyService
from app.modules.listings.application.services import ListingsService


def test_listings_service_import():
    assert ListingsService is not None


def test_companies_service_import():
    assert CreateCompanyService is not None


@pytest.mark.asyncio
async def test_listings_service_smoke():
    class Repo:
        async def get_by_id(self, id):
            return None

        async def list_all(self, page=1, limit=20, company_ids=None):
            return []

        async def count_all(self, company_ids=None):
            return 0

    svc = ListingsService(Repo())
    assert await svc.count_all() == 0
    assert await svc.list_all() == []
    assert await svc.get_by_id("x") is None
