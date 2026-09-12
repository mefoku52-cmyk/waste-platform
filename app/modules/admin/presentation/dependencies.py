"""admin dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.session import get_db_session

from ..application.services import AdminAuditEntryService
from ..infrastructure.repositories import AdminAuditEntryRepositoryImpl


def get_admin_repo(
    session: AsyncSession = Depends(get_db_session),
) -> AdminAuditEntryRepositoryImpl:
    return AdminAuditEntryRepositoryImpl(session)


def get_admin_service(
    repo: AdminAuditEntryRepositoryImpl = Depends(get_admin_repo),
) -> AdminAuditEntryService:
    return AdminAuditEntryService(repository=repo)
