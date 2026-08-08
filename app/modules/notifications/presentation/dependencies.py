"""notifications dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.session import get_db_session

from ..application.services import NotificationService
from ..infrastructure.repositories import NotificationRepositoryImpl


def get_notifications_repo(session: AsyncSession = Depends(get_db_session)) -> NotificationRepositoryImpl:
    return NotificationRepositoryImpl(session)


def get_notifications_service(repo: NotificationRepositoryImpl = Depends(get_notifications_repo)) -> NotificationService:
    return NotificationService(repository=repo)
