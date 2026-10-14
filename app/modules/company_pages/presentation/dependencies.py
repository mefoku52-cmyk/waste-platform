"""company_pages dependency wiring."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.company_pages.application.services import (
    CompanyPageService,
    CompanyPhotoService,
)
from app.modules.company_pages.infrastructure.repositories import (
    CompanyPageRepositoryImpl,
    CompanyPhotoRepositoryImpl,
)
from app.shared.application.clock import Clock
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.infrastructure.db.session import get_db_session


def get_page_repo(
    session: AsyncSession = Depends(get_db_session),
) -> CompanyPageRepositoryImpl:
    return CompanyPageRepositoryImpl(session)


def get_photo_repo(
    session: AsyncSession = Depends(get_db_session),
) -> CompanyPhotoRepositoryImpl:
    return CompanyPhotoRepositoryImpl(session)


def get_company_page_service(
    repo: CompanyPageRepositoryImpl = Depends(get_page_repo),
) -> CompanyPageService:
    return CompanyPageService(
        repo=repo,
        uuid_generator=UuidGenerator(),
        clock=Clock(),
    )


def get_company_photo_service(
    repo: CompanyPhotoRepositoryImpl = Depends(get_photo_repo),
    page_repo: CompanyPageRepositoryImpl = Depends(get_page_repo),
) -> CompanyPhotoService:
    return CompanyPhotoService(
        repo=repo,
        page_repo=page_repo,
        uuid_generator=UuidGenerator(),
        clock=Clock(),
    )
