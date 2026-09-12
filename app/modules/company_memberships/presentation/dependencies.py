from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.company_memberships.application.services import (
    CreateCompanyMembershipService,
    ListCompanyMembershipsService,
    TransitionCompanyMembershipStatusService,
    UpdateCompanyMembershipService,
)
from app.modules.company_memberships.infrastructure.repositories import (
    SqlAlchemyCompanyMembershipRepository,
)
from app.shared.application.clock import Clock
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.infrastructure.db.session import get_db_session


def get_membership_repo(
    session: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyCompanyMembershipRepository:
    return SqlAlchemyCompanyMembershipRepository(session)


def get_create_membership_service(
    repo: SqlAlchemyCompanyMembershipRepository = Depends(get_membership_repo),
) -> CreateCompanyMembershipService:
    return CreateCompanyMembershipService(repo=repo, uuid_generator=UuidGenerator(), clock=Clock())


def get_list_memberships_service(
    repo: SqlAlchemyCompanyMembershipRepository = Depends(get_membership_repo),
) -> ListCompanyMembershipsService:
    return ListCompanyMembershipsService(repo=repo)


def get_update_membership_service(
    repo: SqlAlchemyCompanyMembershipRepository = Depends(get_membership_repo),
) -> UpdateCompanyMembershipService:
    return UpdateCompanyMembershipService(repo=repo, clock=Clock())


def get_transition_membership_status_service(
    repo: SqlAlchemyCompanyMembershipRepository = Depends(get_membership_repo),
) -> TransitionCompanyMembershipStatusService:
    return TransitionCompanyMembershipStatusService(repo=repo, clock=Clock())
