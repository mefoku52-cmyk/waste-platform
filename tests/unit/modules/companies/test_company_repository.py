"""Testy pre SqlAlchemyCompanyRepository.

Zamerne netestujeme konstrukciu Company entity (25 povinnych poli) — to je
uloha pre domain testy. Tu testujeme iba query vrstvu repozitara.
"""

import pytest

from app.modules.companies.infrastructure.repositories import SqlAlchemyCompanyRepository


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_missing(db_session):
    repo = SqlAlchemyCompanyRepository(db_session)
    assert await repo.get_by_id(999999) is None


@pytest.mark.asyncio
async def test_list_returns_empty_tuple_on_empty_table(db_session):
    repo = SqlAlchemyCompanyRepository(db_session)
    items, total = await repo.list()
    assert isinstance(items, list)
    assert total == 0


@pytest.mark.asyncio
async def test_list_empty_company_ids_returns_empty(db_session):
    repo = SqlAlchemyCompanyRepository(db_session)
    items, total = await repo.list(company_ids=[])
    assert items == []
    assert total == 0


@pytest.mark.asyncio
async def test_list_with_pagination_params(db_session):
    repo = SqlAlchemyCompanyRepository(db_session)
    items, total = await repo.list(page=1, page_size=10)
    assert isinstance(items, list)
    assert total == 0
