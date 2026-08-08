"""inquiries dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.session import get_db_session

from ..application.services import InquiryService
from ..infrastructure.repositories import InquiryRepositoryImpl


def get_inquiries_repo(session: AsyncSession = Depends(get_db_session)) -> InquiryRepositoryImpl:
    return InquiryRepositoryImpl(session)


def get_inquiries_service(repo: InquiryRepositoryImpl = Depends(get_inquiries_repo)) -> InquiryService:
    return InquiryService(repository=repo)
