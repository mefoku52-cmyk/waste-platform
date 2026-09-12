"""documents dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.session import get_db_session

from ..application.services import DocumentService
from ..infrastructure.repositories import DocumentRepositoryImpl


def get_documents_repo(
    session: AsyncSession = Depends(get_db_session),
) -> DocumentRepositoryImpl:
    return DocumentRepositoryImpl(session)


def get_documents_service(
    repo: DocumentRepositoryImpl = Depends(get_documents_repo),
) -> DocumentService:
    return DocumentService(repository=repo)
