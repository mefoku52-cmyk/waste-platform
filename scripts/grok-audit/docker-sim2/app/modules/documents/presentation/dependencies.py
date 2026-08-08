"""documents dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.session import get_db
from ..infrastructure.repositories import DocumentsRepositoryImpl
from ..application.services import DocumentsService


async def get_documents_service(
    session: AsyncSession = Depends(get_db)
) -> DocumentsService:
    """Get documents service."""
    repository = DocumentsRepositoryImpl(session)
    return DocumentsService(repository)
