"""compliance dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.session import get_db
from ..infrastructure.repositories import ComplianceRepositoryImpl
from ..application.services import ComplianceService


async def get_compliance_service(
    session: AsyncSession = Depends(get_db)
) -> ComplianceService:
    """Get compliance service."""
    repository = ComplianceRepositoryImpl(session)
    return ComplianceService(repository)
