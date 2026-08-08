"""inquiries dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.session import get_db
from ..infrastructure.repositories import InquiriesRepositoryImpl
from ..application.services import InquiriesService


async def get_inquiries_service(
    session: AsyncSession = Depends(get_db)
) -> InquiriesService:
    """Get inquiries service."""
    repository = InquiriesRepositoryImpl(session)
    return InquiriesService(repository)
