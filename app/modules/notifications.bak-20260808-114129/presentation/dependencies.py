"""notifications dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.session import get_db
from ..infrastructure.repositories import NotificationsRepositoryImpl
from ..application.services import NotificationsService


async def get_notifications_service(
    session: AsyncSession = Depends(get_db)
) -> NotificationsService:
    """Get notifications service."""
    repository = NotificationsRepositoryImpl(session)
    return NotificationsService(repository)
