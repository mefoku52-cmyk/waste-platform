"""admin dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.session import get_db
from ..infrastructure.repositories import AdminRepositoryImpl
from ..application.services import AdminService


async def get_admin_service(
    session: AsyncSession = Depends(get_db)
) -> AdminService:
    """Get admin service."""
    repository = AdminRepositoryImpl(session)
    return AdminService(repository)
