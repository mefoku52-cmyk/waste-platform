"""analytics dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.session import get_db_session

from ..application.services import AnalyticsEventService
from ..infrastructure.repositories import AnalyticsEventRepositoryImpl


def get_analytics_repo(session: AsyncSession = Depends(get_db_session)) -> AnalyticsEventRepositoryImpl:
    return AnalyticsEventRepositoryImpl(session)


def get_analytics_service(repo: AnalyticsEventRepositoryImpl = Depends(get_analytics_repo)) -> AnalyticsEventService:
    return AnalyticsEventService(repository=repo)
