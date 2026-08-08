from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.session import get_db_session
from app.shared.models.base import Company
from app.shared.repositories.base_repository import BaseRepository
from app.modules.companies.domain.service import CompanyService

def get_company_repo(session: AsyncSession = Depends(get_db_session)):
    return BaseRepository(Company, session)

def get_company_service(repo = Depends(get_company_repo)):
    return CompanyService(repository=repo)
