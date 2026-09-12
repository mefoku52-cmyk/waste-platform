"""Rozšírené unit testy pre users application services."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.users.application.services import (
    CreateUserService,
    TransitionUserStatusService,
    UpdateUserService,
)
from app.modules.users.domain.entities import User
from app.modules.users.domain.enums import UserStatus
from app.shared.domain.exceptions import ConflictDomainError, NotFoundDomainError


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
    """Mock clock."""
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
    repo.get_by_email = AsyncMock(return_value=None)
    repo.list = AsyncMock(return_value=([], 0))
    repo.update = AsyncMock(return_value=None)
    repo.count = AsyncMock(return_value=0)
    return repo


@pytest.fixture
def mock_uuid_gen():
    """Mock UUID generator."""
    gen = MagicMock()
    gen.new.return_value = uuid4()
    return gen


# === CreateUserService ===


@pytest.mark.asyncio
async def test_create_user_success(mock_repo, mock_uuid_gen):
    """CreateUserService vytvorí usera."""
    mock_repo.get_by_email.return_value = None

    service = CreateUserService(
        repo=mock_repo,
        uuid_generator=mock_uuid_gen,
        clock=_make_clock(),
    )
    result = await service.execute(
        email="New@Example.com",
        password_hash="hashed",
        first_name="  Ján  ",
        last_name="  Novák  ",
        display_name=None,
        phone=None,
        locale=None,
        timezone=None,
        actor_user_id=uuid4(),
    )

    assert result.email == "new@example.com"  # lowercase + strip
    assert result.first_name == "Ján"  # strip
    mock_repo.add.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_conflict(mock_repo, mock_uuid_gen):
    """CreateUserService hodí Conflict ak email existuje."""
    mock_repo.get_by_email.return_value = _make_user()

    service = CreateUserService(
        repo=mock_repo,
        uuid_generator=mock_uuid_gen,
        clock=_make_clock(),
    )
    with pytest.raises(ConflictDomainError):
        await service.execute(
            email="existing@example.com",
            password_hash="hashed",
            first_name="Ján",
            last_name="Novák",
            display_name=None,
            phone=None,
            locale=None,
            timezone=None,
            actor_user_id=None,
        )


# === UpdateUserService ===


@pytest.mark.asyncio
async def test_update_user_success(mock_repo):
    """UpdateUserService updatne usera."""
    user = _make_user(first_name="Staré", last_name="Meno")
    mock_repo.get_by_id.return_value = user

    service = UpdateUserService(repo=mock_repo, clock=_make_clock())
    result = await service.execute(
        user_id=user.id,
        first_name="Nové",
        last_name="Meno",
        display_name="Nick",
        phone="+421900000000",
        locale="sk",
        timezone="Europe/Bratislava",
        actor_user_id=uuid4(),
    )

    assert result.first_name == "Nové"
    assert result.display_name == "Nick"
    mock_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_not_found(mock_repo):
    """UpdateUserService hodí NotFound."""
    mock_repo.get_by_id.return_value = None

    service = UpdateUserService(repo=mock_repo, clock=_make_clock())
    with pytest.raises(NotFoundDomainError):
        await service.execute(
            user_id=uuid4(),
            first_name="X",
            last_name="Y",
            display_name=None,
            phone=None,
            locale=None,
            timezone=None,
            actor_user_id=None,
        )


@pytest.mark.asyncio
async def test_update_user_partial(mock_repo):
    """UpdateUserService updatne iba zadané polia."""
    user = _make_user(first_name="Pôvodné", last_name="Meno")
    mock_repo.get_by_id.return_value = user

    service = UpdateUserService(repo=mock_repo, clock=_make_clock())
    result = await service.execute(
        user_id=user.id,
        first_name=None,  # nezmení sa
        last_name=None,
        display_name="NovýNick",
        phone=None,
        locale=None,
        timezone=None,
        actor_user_id=None,
    )

    assert result.first_name == "Pôvodné"  # nezmenené
    assert result.display_name == "NovýNick"


# === TransitionUserStatusService ===


@pytest.mark.asyncio
async def test_transition_user_status_success(mock_repo):
    """TransitionUserStatusService zmení status."""
    user = _make_user(status=UserStatus.ACTIVE)
    mock_repo.get_by_id.return_value = user

    service = TransitionUserStatusService(repo=mock_repo, clock=_make_clock())
    result = await service.execute(
        user_id=user.id,
        to_status="suspended",
        actor_user_id=uuid4(),
    )

    assert result.status == UserStatus.SUSPENDED
    mock_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_transition_user_status_not_found(mock_repo):
    """TransitionUserStatusService hodí NotFound."""
    mock_repo.get_by_id.return_value = None

    service = TransitionUserStatusService(repo=mock_repo, clock=_make_clock())
    with pytest.raises(NotFoundDomainError):
        await service.execute(
            user_id=uuid4(),
            to_status="suspended",
            actor_user_id=None,
        )
