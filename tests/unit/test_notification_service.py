"""Unit tests for NotificationService.

The service owns the read/unread state machine and delegates persistence to the
repository. These tests pin the real repository contract:

    mark_read:   get_by_id -> set is_read -> update
    mark_unread: get_by_id -> clear is_read -> update

There is no ``repository.mark_read`` method; an earlier version of this file
mocked one and therefore failed with ``'MagicMock' object can't be awaited``.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.notifications.application.services import NotificationService
from app.modules.notifications.domain.entities import NotificationEntity
from app.shared.domain.exceptions import NotFoundDomainError, ValidationDomainError


def _notification(**over):
    base = {
        "user_id": uuid4(),
        "type": "inquiry_received",
        "title": "Novy dopyt",
        "message": "Mate novy dopyt na inzerat",
        "is_read": False,
    }
    base.update(over)
    return NotificationEntity(**base)


def _repo(**methods):
    repo = MagicMock()
    for name, value in methods.items():
        setattr(repo, name, value)
    return repo


# --------------------------------------------------------------------------
# read paths
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_by_id_delegates():
    entity = _notification()
    repo = _repo(get_by_id=AsyncMock(return_value=entity))
    svc = NotificationService(repo)

    assert await svc.get_by_id(str(entity.id)) is entity
    repo.get_by_id.assert_awaited_once_with(str(entity.id))


@pytest.mark.asyncio
async def test_get_by_id_returns_none():
    repo = _repo(get_by_id=AsyncMock(return_value=None))
    svc = NotificationService(repo)

    assert await svc.get_by_id(str(uuid4())) is None


@pytest.mark.asyncio
async def test_list_all_delegates():
    repo = _repo(list_all=AsyncMock(return_value=[]))
    svc = NotificationService(repo)

    assert await svc.list_all(2, 5) == []
    repo.list_all.assert_awaited_once_with(2, 5)


@pytest.mark.asyncio
async def test_list_by_user_id_delegates():
    repo = _repo(list_by_user_id=AsyncMock(return_value=[]))
    svc = NotificationService(repo)
    uid = uuid4()

    assert await svc.list_by_user_id(uid, 1, 10) == []
    repo.list_by_user_id.assert_awaited_once_with(uid, 1, 10)


@pytest.mark.asyncio
async def test_count_by_user_id_delegates():
    repo = _repo(count_by_user_id=AsyncMock(return_value=7))
    svc = NotificationService(repo)

    assert await svc.count_by_user_id(uuid4()) == 7


@pytest.mark.asyncio
async def test_count_all_delegates():
    repo = _repo(count_all=AsyncMock(return_value=42))
    svc = NotificationService(repo)

    assert await svc.count_all() == 42


@pytest.mark.asyncio
async def test_count_unread_delegates():
    repo = _repo(count_unread=AsyncMock(return_value=5))
    svc = NotificationService(repo)

    assert await svc.count_unread(uuid4()) == 5
    repo.count_unread.assert_awaited_once()


@pytest.mark.asyncio
async def test_count_unread_zero():
    repo = _repo(count_unread=AsyncMock(return_value=0))
    svc = NotificationService(repo)

    assert await svc.count_unread(uuid4()) == 0


# --------------------------------------------------------------------------
# create
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_delegates_to_repo():
    entity = _notification()
    repo = _repo(create=AsyncMock(return_value=entity))
    svc = NotificationService(repo)

    assert await svc.create(entity) is entity
    repo.create.assert_awaited_once_with(entity)


@pytest.mark.asyncio
async def test_create_validates_before_touching_repo():
    """An invalid entity must not reach the repository."""
    repo = _repo(create=AsyncMock())
    svc = NotificationService(repo)

    with pytest.raises(ValidationDomainError):
        await svc.create(_notification(message=""))

    repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_rejects_blank_type():
    repo = _repo(create=AsyncMock())
    svc = NotificationService(repo)

    with pytest.raises(ValidationDomainError):
        await svc.create(_notification(type=""))

    repo.create.assert_not_awaited()


# --------------------------------------------------------------------------
# mark_read / mark_unread
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mark_read_not_found():
    repo = _repo(get_by_id=AsyncMock(return_value=None), update=AsyncMock())
    svc = NotificationService(repo)

    with pytest.raises(NotFoundDomainError):
        await svc.mark_read(str(uuid4()))

    repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_mark_read_sets_flag_and_persists():
    entity = _notification(is_read=False)
    repo = _repo(
        get_by_id=AsyncMock(return_value=entity),
        update=AsyncMock(side_effect=lambda e: e),
    )
    svc = NotificationService(repo)

    result = await svc.mark_read(str(entity.id))

    assert result.is_read is True
    assert entity.is_read is True
    repo.update.assert_awaited_once_with(entity)


@pytest.mark.asyncio
async def test_mark_read_is_idempotent():
    entity = _notification(is_read=True)
    repo = _repo(
        get_by_id=AsyncMock(return_value=entity),
        update=AsyncMock(side_effect=lambda e: e),
    )
    svc = NotificationService(repo)

    assert (await svc.mark_read(str(entity.id))).is_read is True


@pytest.mark.asyncio
async def test_mark_unread_not_found():
    repo = _repo(get_by_id=AsyncMock(return_value=None), update=AsyncMock())
    svc = NotificationService(repo)

    with pytest.raises(NotFoundDomainError):
        await svc.mark_unread(str(uuid4()))

    repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_mark_unread_clears_flag_and_persists():
    entity = _notification(is_read=True)
    repo = _repo(
        get_by_id=AsyncMock(return_value=entity),
        update=AsyncMock(side_effect=lambda e: e),
    )
    svc = NotificationService(repo)

    result = await svc.mark_unread(str(entity.id))

    assert result.is_read is False
    repo.update.assert_awaited_once_with(entity)


# --------------------------------------------------------------------------
# delete
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_not_found():
    repo = _repo(get_by_id=AsyncMock(return_value=None), delete=AsyncMock())
    svc = NotificationService(repo)

    with pytest.raises(NotFoundDomainError):
        await svc.delete(str(uuid4()))

    repo.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_delegates():
    entity = _notification()
    repo = _repo(get_by_id=AsyncMock(return_value=entity), delete=AsyncMock())
    svc = NotificationService(repo)

    await svc.delete(str(entity.id))

    repo.delete.assert_awaited_once_with(str(entity.id))
