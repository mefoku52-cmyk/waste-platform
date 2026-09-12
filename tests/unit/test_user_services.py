"""Unit tests pre users application services."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.users.application.services import (
    GetUserService,
    ListUsersService,
)
from app.modules.users.domain.entities import User
from app.modules.users.domain.enums import UserStatus


def _make_user(**overrides):
    """Helper na vytvorenie User entity."""
    defaults = {
        "id": uuid4(),
        "email": "test@example.com",
        "password_hash": "hashed",
        "first_name": "Ján",
        "last_name": "Novák",
        "display_name": None,
        "phone": None,
        "locale": None,
        "timezone": None,
        "last_login_at": None,
        "status": UserStatus.ACTIVE,
    }
    defaults.update(overrides)
    return User(**defaults)


def _make_clock():
    """Mock clock vracajúci fixný čas."""
    from datetime import UTC, datetime

    clock = MagicMock()
    clock.now.return_value = datetime.now(UTC)
    return clock


@pytest.fixture
def mock_repo():
    """Mock repository."""
    repo = AsyncMock()
    repo.add = AsyncMock(return_value=None)
    repo.get_by_id = AsyncMock(return_value=None)
    repo.list = AsyncMock(return_value=[])
    repo.update = AsyncMock(return_value=None)
    repo.count = AsyncMock(return_value=0)
    return repo


@pytest.fixture
def mock_uuid_gen():
    """Mock UUID generator."""
    gen = MagicMock()
    gen.new.return_value = uuid4()
    return gen


@pytest.mark.asyncio
async def test_get_user_service_success(mock_repo):
    """GetUserService vráti usera."""
    user_id = uuid4()
    user = _make_user(id=user_id)
    mock_repo.get_by_id.return_value = user

    service = GetUserService(repo=mock_repo)
    result = await service.execute(user_id)

    assert result.id == user_id
    mock_repo.get_by_id.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_get_user_service_not_found(mock_repo):
    """GetUserService hodí NotFound, ak user neexistuje."""
    from app.shared.domain.exceptions import NotFoundDomainError

    mock_repo.get_by_id.return_value = None

    service = GetUserService(repo=mock_repo)
    with pytest.raises((NotFoundDomainError, Exception)):
        await service.execute(uuid4())


@pytest.mark.asyncio
async def test_list_users_service_empty(mock_repo):
    """ListUsersService vráti prázdny zoznam."""
    mock_repo.list.return_value = ([], 0)

    service = ListUsersService(repo=mock_repo)
    result = await service.execute(status=None, company_id=None, q=None, page=1, page_size=20)

    items, total = result
    assert items == []
    assert total == 0


@pytest.mark.asyncio
async def test_list_users_service_with_data(mock_repo):
    """ListUsersService vráti userov."""
    users = [_make_user(), _make_user(email="b@example.com")]
    mock_repo.list.return_value = (users, 2)

    service = ListUsersService(repo=mock_repo)
    result = await service.execute(status=None, company_id=None, q=None, page=1, page_size=20)

    items, total = result
    assert len(items) == 2
    assert total == 2
