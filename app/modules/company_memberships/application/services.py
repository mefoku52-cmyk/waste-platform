from uuid import UUID

from app.modules.company_memberships.application.dto import CompanyMembershipDTO
from app.modules.company_memberships.application.mappers import to_membership_dto
from app.modules.company_memberships.domain.entities import CompanyMembership
from app.modules.company_memberships.domain.enums import (
    CompanyMembershipRole,
    CompanyMembershipStatus,
)
from app.modules.company_memberships.domain.repositories import (
    CompanyMembershipRepository,
)
from app.shared.application.clock import Clock
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.domain.exceptions import NotFoundDomainError


class CreateCompanyMembershipService:
    def __init__(
        self,
        repo: CompanyMembershipRepository,
        uuid_generator: UuidGenerator,
        clock: Clock,
    ):
        self.repo = repo
        self.uuid_generator = uuid_generator
        self.clock = clock

    async def execute(
        self,
        *,
        company_id: UUID,
        user_id: UUID,
        membership_role: str,
        is_primary_contact: bool,
        actor_user_id: UUID | None,
    ) -> CompanyMembershipDTO:
        now = self.clock.now()
        membership = CompanyMembership(
            id=self.uuid_generator.new(),
            status=CompanyMembershipStatus.ACTIVE,
            company_id=company_id,
            user_id=user_id,
            membership_role=CompanyMembershipRole(membership_role),
            is_primary_contact=is_primary_contact,
            invited_at=now,
            joined_at=now,
            left_at=None,
            created_at=now,
            created_by_user_id=actor_user_id,
            updated_at=now,
            updated_by_user_id=actor_user_id,
        )
        membership.validate()
        await self.repo.add(membership)
        return to_membership_dto(membership)


class ListCompanyMembershipsService:
    def __init__(self, repo: CompanyMembershipRepository):
        self.repo = repo

    async def execute(self, *, company_id: UUID, status: str | None) -> list[CompanyMembershipDTO]:
        items = await self.repo.list_by_company_id(company_id, status)
        return [to_membership_dto(item) for item in items]


class UpdateCompanyMembershipService:
    def __init__(self, repo: CompanyMembershipRepository, clock: Clock):
        self.repo = repo
        self.clock = clock

    async def execute(
        self,
        *,
        membership_id: UUID,
        membership_role: str | None,
        is_primary_contact: bool | None,
        actor_user_id: UUID | None,
    ) -> CompanyMembershipDTO:
        membership = await self.repo.get_by_id(membership_id)
        if not membership:
            raise NotFoundDomainError("Company membership not found")
        if membership_role is not None:
            membership.membership_role = CompanyMembershipRole(membership_role)
        if is_primary_contact is not None:
            membership.is_primary_contact = is_primary_contact
        membership.updated_at = self.clock.now()
        membership.updated_by_user_id = actor_user_id
        await self.repo.update(membership)
        return to_membership_dto(membership)


class TransitionCompanyMembershipStatusService:
    def __init__(self, repo: CompanyMembershipRepository, clock: Clock):
        self.repo = repo
        self.clock = clock

    async def execute(
        self, *, membership_id: UUID, to_status: str, actor_user_id: UUID | None
    ) -> CompanyMembershipDTO:
        membership = await self.repo.get_by_id(membership_id)
        if not membership:
            raise NotFoundDomainError("Company membership not found")
        membership.transition_status(CompanyMembershipStatus(to_status))
        membership.updated_at = self.clock.now()
        membership.updated_by_user_id = actor_user_id
        await self.repo.update(membership)
        return to_membership_dto(membership)
