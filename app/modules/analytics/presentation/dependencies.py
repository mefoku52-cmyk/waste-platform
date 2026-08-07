"""analytics dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.session import get_db
from ..infrastructure.repositories import AnalyticsRepositoryImpl
from ..application.services import AnalyticsService


async def get_analytics_service(
    session: AsyncSession = Depends(get_db)
) -> AnalyticsService:
    """Get analytics service."""
    repository = AnalyticsRepositoryImpl(session)
    return AnalyticsService(repository)
