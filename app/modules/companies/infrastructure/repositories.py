from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.domain.entities import Company
from app.modules.companies.domain.repositories import CompanyRepository
from app.modules.companies.infrastructure.mappers import to_domain, to_model
from app.modules.companies.infrastructure.models import CompanyModel


class SqlAlchemyCompanyRepository(CompanyRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, company: Company) -> None:
        self.session.add(to_model(company))
        await self.session.commit()

    async def get_by_id(self, company_id):
        stmt = select(CompanyModel).where(CompanyModel.id == str(company_id))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def list(
        self,
        *,
        status,
        company_type,
        seller_capability,
        buyer_capability,
        logistics_capability,
        q,
        page,
        page_size,
        company_ids=None,
    ):
        stmt = select(CompanyModel)
        count_stmt = select(func.count()).select_from(CompanyModel)

        if company_ids is not None:
            ids = [str(x) for x in company_ids]
            if not ids:
                return [], 0
            stmt = stmt.where(CompanyModel.id.in_(ids))
            count_stmt = count_stmt.where(CompanyModel.id.in_(ids))

        if status:
            stmt = stmt.where(CompanyModel.status == status)
            count_stmt = count_stmt.where(CompanyModel.status == status)
        if company_type:
            stmt = stmt.where(CompanyModel.company_type == company_type)
            count_stmt = count_stmt.where(CompanyModel.company_type == company_type)
        if seller_capability is not None:
            stmt = stmt.where(CompanyModel.seller_capability == seller_capability)
            count_stmt = count_stmt.where(CompanyModel.seller_capability == seller_capability)
        if buyer_capability is not None:
            stmt = stmt.where(CompanyModel.buyer_capability == buyer_capability)
            count_stmt = count_stmt.where(CompanyModel.buyer_capability == buyer_capability)
        if logistics_capability is not None:
            stmt = stmt.where(CompanyModel.logistics_capability == logistics_capability)
            count_stmt = count_stmt.where(CompanyModel.logistics_capability == logistics_capability)
        if q:
            pattern = f"%{q}%"
            expr = or_(
                CompanyModel.legal_name.ilike(pattern),
                CompanyModel.trading_name.ilike(pattern),
                CompanyModel.registration_number.ilike(pattern),
            )
            stmt = stmt.where(expr)
            count_stmt = count_stmt.where(expr)

        stmt = stmt.order_by(CompanyModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        rows = (await self.session.execute(stmt)).scalars().all()
        total = (await self.session.execute(count_stmt)).scalar_one()
        return [to_domain(row) for row in rows], int(total)

    async def update(self, company: Company) -> None:
        model = await self.session.get(CompanyModel, str(company.id))
        if model is None:
            return
        model.status = company.status.value
        model.legal_name = company.legal_name
        model.trading_name = company.trading_name
        model.tax_identifier = company.tax_identifier
        model.email = company.email
        model.phone = company.phone
        model.website_url = company.website_url
        model.address_line_1 = company.address_line_1
        model.address_line_2 = company.address_line_2
        model.city = company.city
        model.postal_code = company.postal_code
        model.latitude = company.latitude
        model.longitude = company.longitude
        model.verification_submitted_at = company.verification_submitted_at
        model.verification_reviewed_at = company.verification_reviewed_at
        model.verification_reviewed_by_user_id = (
            str(company.verification_reviewed_by_user_id) if company.verification_reviewed_by_user_id else None
        )
        model.verified_at = company.verified_at
        model.verified_by_user_id = str(company.verified_by_user_id) if company.verified_by_user_id else None
        model.rejected_at = company.rejected_at
        model.rejected_by_user_id = str(company.rejected_by_user_id) if company.rejected_by_user_id else None
        model.updated_at = company.updated_at
        model.updated_by_user_id = str(company.updated_by_user_id) if company.updated_by_user_id else None
        await self.session.commit()
