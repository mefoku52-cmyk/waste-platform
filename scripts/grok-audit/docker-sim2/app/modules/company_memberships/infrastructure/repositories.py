from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.company_memberships.domain.entities import CompanyMembership
from app.modules.company_memberships.domain.repositories import CompanyMembershipRepository
from app.modules.company_memberships.infrastructure.mappers import to_domain, to_model
from app.modules.company_memberships.infrastructure.models import CompanyMembershipModel


class SqlAlchemyCompanyMembershipRepository(CompanyMembershipRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, membership: CompanyMembership) -> None:
        self.session.add(to_model(membership))
        await self.session.commit()

    async def get_by_id(self, membership_id: UUID) -> CompanyMembership | None:
        stmt = select(CompanyMembershipModel).where(CompanyMembershipModel.id == str(membership_id))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def list_by_company_id(self, company_id: UUID, status: str | None = None) -> list[CompanyMembership]:
        stmt = select(CompanyMembershipModel).where(CompanyMembershipModel.company_id == str(company_id))
        if status:
            stmt = stmt.where(CompanyMembershipModel.status == status)
        stmt = stmt.order_by(CompanyMembershipModel.created_at.desc())
        result = await self.session.execute(stmt)
        return [to_domain(item) for item in result.scalars().all()]

    async def list_by_user_id(self, user_id: UUID) -> list[CompanyMembership]:
        stmt = select(CompanyMembershipModel).where(CompanyMembershipModel.user_id == str(user_id))
        stmt = stmt.order_by(CompanyMembershipModel.created_at.desc())
        result = await self.session.execute(stmt)
        return [to_domain(item) for item in result.scalars().all()]

    async def update(self, membership: CompanyMembership) -> None:
        model = await self.session.get(CompanyMembershipModel, str(membership.id))
        if model is None:
            return
        model.status = membership.status.value
        model.membership_role = membership.membership_role.value
        model.is_primary_contact = membership.is_primary_contact
        model.invited_at = membership.invited_at
        model.joined_at = membership.joined_at
        model.left_at = membership.left_at
        model.updated_at = membership.updated_at
        model.updated_by_user_id = str(membership.updated_by_user_id) if membership.updated_by_user_id else None
        await self.session.commit()
