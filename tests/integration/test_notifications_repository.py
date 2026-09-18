"""Integration tests for the notifications repository against a real database.

These run against the SQLite database configured in ``tests/conftest.py``
(``sqlite+aiosqlite:///./var/test.db``). Every test creates its own user id and
removes the rows it created, so the suite stays re-runnable and never asserts on
globally shared row counts.
"""

import contextlib
from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.modules.notifications.domain.entities import NotificationEntity
from app.modules.notifications.infrastructure.repositories import (
    NotificationRepositoryImpl,
)
from app.shared.infrastructure.db.session import async_session_maker

pytestmark = pytest.mark.integration


def _entity(**over):
    base = {
        "id": uuid4(),
        "user_id": uuid4(),
        "type": "inquiry_received",
        "title": "Novy dopyt",
        "message": "Mate novy dopyt na vas inzerat",
        "is_read": False,
        "related_entity_id": None,
        "created_at": datetime(2026, 9, 17, 10, 0, 0),
        "updated_at": datetime(2026, 9, 17, 10, 0, 0),
        "created_by_user_id": None,
        "updated_by_user_id": None,
    }
    base.update(over)
    return NotificationEntity(**base)


@pytest.fixture
async def session():
    async with async_session_maker() as s:
        yield s


@pytest.fixture
async def repo(session):
    return NotificationRepositoryImpl(session)


@pytest.fixture
async def cleanup(repo):
    """Delete everything created during a test, even on failure.

    Ids are tracked as UUID objects: ``delete`` binds the value straight onto a
    ``UUID(as_uuid=True)`` column, which raises on dialects without native UUID
    support (e.g. SQLite) when handed a plain string.
    """
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
    assert fetched.user_id == entity.user_id
    assert fetched.title == entity.title
    assert fetched.message == entity.message
    assert fetched.is_read is False


async def test_get_by_id_returns_none_for_unknown_id(repo):
    assert await repo.get_by_id(uuid4()) is None


async def test_create_persists_optional_related_entity_id(repo, cleanup):
    related = uuid4()
    entity = _entity(related_entity_id=related)
    cleanup.append(entity.id)

    created = await repo.create(entity)

    assert (await repo.get_by_id(created.id)).related_entity_id == related


async def test_count_unread_counts_only_unread_for_that_user(repo, cleanup):
    user = uuid4()
    read = _entity(user_id=user, is_read=True)
    unread_a = _entity(user_id=user, is_read=False)
    unread_b = _entity(user_id=user, is_read=False)
    other_user = _entity(user_id=uuid4(), is_read=False)
    for e in (read, unread_a, unread_b, other_user):
        cleanup.append(e.id)
        await repo.create(e)

    assert await repo.count_unread(user) == 2
    assert await repo.count_unread(other_user.user_id) == 1


async def test_count_by_user_id_includes_read_and_unread(repo, cleanup):
    user = uuid4()
    for e in (_entity(user_id=user, is_read=True), _entity(user_id=user)):
        cleanup.append(e.id)
        await repo.create(e)

    assert await repo.count_by_user_id(user) == 2


async def test_update_persists_is_read_transition(repo, cleanup):
    user = uuid4()
    entity = _entity(user_id=user, is_read=False)
    cleanup.append(entity.id)
    created = await repo.create(entity)
    assert await repo.count_unread(user) == 1

    created.is_read = True
    updated = await repo.update(created)

    assert updated.is_read is True
    assert await repo.count_unread(user) == 0


async def test_list_by_user_id_is_scoped_and_newest_first(repo, cleanup):
    user = uuid4()
    base = datetime(2026, 9, 17, 10, 0, 0)
    older = _entity(user_id=user, created_at=base)
    newer = _entity(user_id=user, created_at=base + timedelta(hours=1), title="Novsi")
    for e in (older, newer):
        cleanup.append(e.id)
        await repo.create(e)

    listed = await repo.list_by_user_id(user, page=1, limit=10)

    assert [n.id for n in listed] == [newer.id, older.id]


async def test_list_by_user_id_paginates(repo, cleanup):
    user = uuid4()
    base = datetime(2026, 9, 17, 10, 0, 0)
    for offset in range(3):
        e = _entity(user_id=user, created_at=base + timedelta(hours=offset))
        cleanup.append(e.id)
        await repo.create(e)

    first_page = await repo.list_by_user_id(user, page=1, limit=2)
    second_page = await repo.list_by_user_id(user, page=2, limit=2)

    assert len(first_page) == 2
    assert len(second_page) == 1
    assert {n.id for n in first_page}.isdisjoint({n.id for n in second_page})


async def test_delete_removes_the_row(repo, cleanup):
    entity = _entity()
    created = await repo.create(entity)

    await repo.delete(created.id)

    assert await repo.get_by_id(created.id) is None


async def test_create_and_delete_move_global_counters(repo):
    before_all = await repo.count_all()

    entity = _entity()
    await repo.create(entity)
    assert await repo.count_all() == before_all + 1

    await repo.delete(entity.id)
    assert await repo.count_all() == before_all


async def test_list_all_includes_created_row(repo, cleanup):
    entity = _entity()
    cleanup.append(entity.id)
    await repo.create(entity)

    listed = await repo.list_all(page=1, limit=100)

    assert entity.id in {n.id for n in listed}


@pytest.mark.xfail(
    reason=(
        "get_by_id binds the raw id against a UUID(as_uuid=True) column. On a "
        "dialect without native UUID support (SQLite) the bind processor calls "
        "str.hex and raises StatementError. The service layer passes str, and "
        "Pydantic/schema ids arrive as str in the API layer."
    ),
    strict=False,
)
async def test_get_by_id_accepts_a_string_id(repo, cleanup):
    """Documents a latent bug: sibling repos coerce with uuid.UUID(str(id))."""
    entity = _entity()
    cleanup.append(entity.id)
    created = await repo.create(entity)

    assert await repo.get_by_id(str(created.id)) is not None
