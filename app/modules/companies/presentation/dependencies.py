from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.application.services import (
    CreateCompanyService,
    GetCompanyService,
    ListCompaniesService,
    TransitionCompanyStatusService,
    UpdateCompanyService,
)
from app.modules.companies.infrastructure.repositories import (
    SqlAlchemyCompanyRepository,
)
from app.modules.company_memberships.infrastructure.repositories import (
    SqlAlchemyCompanyMembershipRepository,
)
from app.modules.company_memberships.presentation.dependencies import (
    get_membership_repo,
)
from app.shared.application.clock import Clock
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.infrastructure.db.session import get_db_session


def get_company_repo(
    session: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyCompanyRepository:
    return SqlAlchemyCompanyRepository(session)


def get_create_company_service(
    repo: SqlAlchemyCompanyRepository = Depends(get_company_repo),
    membership_repo: SqlAlchemyCompanyMembershipRepository = Depends(get_membership_repo),
) -> CreateCompanyService:
    return CreateCompanyService(
        repo=repo,
        membership_repo=membership_repo,
        uuid_generator=UuidGenerator(),
        clock=Clock(),
    )


def get_get_company_service(
    repo: SqlAlchemyCompanyRepository = Depends(get_company_repo),
) -> GetCompanyService:
    return GetCompanyService(repo=repo)


def get_list_companies_service(
    repo: SqlAlchemyCompanyRepository = Depends(get_company_repo),
) -> ListCompaniesService:
    return ListCompaniesService(repo=repo)


def get_update_company_service(
    repo: SqlAlchemyCompanyRepository = Depends(get_company_repo),
) -> UpdateCompanyService:
    return UpdateCompanyService(repo=repo, clock=Clock())


def get_transition_company_status_service(
    repo: SqlAlchemyCompanyRepository = Depends(get_company_repo),
) -> TransitionCompanyStatusService:
    return TransitionCompanyStatusService(repo=repo, clock=Clock())
