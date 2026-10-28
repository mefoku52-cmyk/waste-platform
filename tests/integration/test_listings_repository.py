"""Integration tests for the listings repository against a real database."""

import contextlib
from uuid import uuid4

import pytest

from app.modules.listings.domain.entities import ListingsEntity
from app.modules.listings.domain.enums import ListingsStatus
from app.modules.listings.infrastructure.repositories import ListingsRepositoryImpl
from app.shared.infrastructure.db.session import async_session_maker

pytestmark = pytest.mark.integration


def _entity(**over):
    base = {
        "id": uuid4(),
        "title": "Test listing",
        "material_type": "Plastic",
        "quantity": 10.0,
        "unit": "kg",
        "condition": "used",
        "location": "Bratislava",
        "company_id": str(uuid4()),
        "status": ListingsStatus.DRAFT,
        "price": 5.0,
        "currency": "EUR",
        "description": "desc",
    }
    base.update(over)
    return ListingsEntity(**base)


@pytest.fixture
async def session():
    async with async_session_maker() as s:
        yield s


@pytest.fixture
async def repo(session):
    return ListingsRepositoryImpl(session)


@pytest.fixture
async def cleanup(repo):
    created = []
    yield created
    for entity_id in created:
        with contextlib.suppress(Exception):
            await repo.delete(entity_id)


async def test_create_then_get_by_id_round_trip(repo, cleanup):
    entity = _entity()
    cleanup.append(entity.id)

    created = await repo.create(entity)
    fetched = await repo.get_by_id(created.id)

    assert fetched is not None
    assert fetched.id == entity.id
    assert fetched.title == entity.title
    assert fetched.material_type == entity.material_type
    assert fetched.quantity == entity.quantity
    assert fetched.company_id == entity.company_id


async def test_get_by_id_returns_none_for_unknown_id(repo):
    assert await repo.get_by_id(uuid4()) is None


async def test_get_by_id_accepts_string_id(repo, cleanup):
    entity = _entity()
    cleanup.append(entity.id)
    created = await repo.create(entity)

    assert await repo.get_by_id(str(created.id)) is not None


async def test_list_all_includes_created_row(repo, cleanup):
    entity = _entity()
    cleanup.append(entity.id)
    await repo.create(entity)

    listed = await repo.list_all(page=1, limit=100)

    assert entity.id in {row.id for row in listed}


async def test_list_all_paginates(repo, cleanup):
    base_company = str(uuid4())
    for _ in range(3):
        e = _entity(company_id=base_company)
        cleanup.append(e.id)
        await repo.create(e)

    first_page = await repo.list_all(page=1, limit=2, company_ids=[base_company])
    second_page = await repo.list_all(page=2, limit=2, company_ids=[base_company])

    assert len(first_page) == 2
    assert len(second_page) == 1
    assert {r.id for r in first_page}.isdisjoint({r.id for r in second_page})


async def test_delete_removes_the_row(repo, cleanup):
    entity = _entity()
    created = await repo.create(entity)

    await repo.delete(created.id)

    assert await repo.get_by_id(created.id) is None


async def test_count_all_reflects_created_row(repo, cleanup):
    before = await repo.count_all()
    entity = _entity()
    cleanup.append(entity.id)
    await repo.create(entity)

    assert await repo.count_all() == before + 1
