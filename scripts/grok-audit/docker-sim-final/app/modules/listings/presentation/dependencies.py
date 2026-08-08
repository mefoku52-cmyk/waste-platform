"""listings dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.session import get_db
from ..infrastructure.repositories import ListingsRepositoryImpl
from ..application.services import ListingsService


async def get_listings_service(
    session: AsyncSession = Depends(get_db)
) -> ListingsService:
    """Get listings service."""
    repository = ListingsRepositoryImpl(session)
    return ListingsService(repository)
