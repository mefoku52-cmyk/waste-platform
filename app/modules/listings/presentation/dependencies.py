"""listings dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.session import get_db_session

from ..application.services import ListingsService
from ..infrastructure.repositories import ListingsRepositoryImpl


def get_listings_repo(
    session: AsyncSession = Depends(get_db_session),
) -> ListingsRepositoryImpl:
    return ListingsRepositoryImpl(session)


def get_listings_service(
    repo: ListingsRepositoryImpl = Depends(get_listings_repo),
) -> ListingsService:
    return ListingsService(repository=repo)
