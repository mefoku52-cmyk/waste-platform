"""compliance dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.session import get_db_session

from ..application.services import ComplianceRecordService
from ..infrastructure.repositories import ComplianceRecordRepositoryImpl


def get_compliance_repo(
    session: AsyncSession = Depends(get_db_session),
) -> ComplianceRecordRepositoryImpl:
    return ComplianceRecordRepositoryImpl(session)


def get_compliance_service(
    repo: ComplianceRecordRepositoryImpl = Depends(get_compliance_repo),
) -> ComplianceRecordService:
    return ComplianceRecordService(repository=repo)
