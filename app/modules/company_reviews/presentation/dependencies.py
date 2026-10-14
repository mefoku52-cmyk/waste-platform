"""company_reviews dependency wiring."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.company_reviews.application.services import CompanyReviewService
from app.modules.company_reviews.infrastructure.repositories import (
    CompanyReviewRepositoryImpl,
)
from app.shared.application.clock import Clock
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.infrastructure.db.session import get_db_session


def get_review_repo(
    session: AsyncSession = Depends(get_db_session),
) -> CompanyReviewRepositoryImpl:
    return CompanyReviewRepositoryImpl(session)


def get_company_review_service(
    repo: CompanyReviewRepositoryImpl = Depends(get_review_repo),
) -> CompanyReviewService:
    return CompanyReviewService(
        repo=repo,
        uuid_generator=UuidGenerator(),
        clock=Clock(),
    )
