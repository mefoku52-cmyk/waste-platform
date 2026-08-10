"""inquiries repository implementations."""

from typing import List, Optional

from sqlalchemy import delete as sql_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.entities import InquiryEntity
from ..domain.repositories import InquiryRepository
from .mappers import to_domain, to_model
from .models import InquiryModel
from app.modules.listings.infrastructure.models import ListingsModel


class InquiryRepositoryImpl(InquiryRepository):
    """Inquiry repository implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: str) -> Optional[InquiryEntity]:
        result = await self.session.execute(select(InquiryModel).where(InquiryModel.id == id))
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def list_all(self, page: int = 1, limit: int = 20) -> List[InquiryEntity]:
        offset = (page - 1) * limit
        result = await self.session.execute(select(InquiryModel).order_by(InquiryModel.created_at.desc()).offset(offset).limit(limit))
        models = result.scalars().all()
        return [to_domain(m) for m in models]

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(InquiryModel))
        return int(result.scalar_one())


    async def list_sent(self, page: int = 1, limit: int = 20, company_ids=None) -> list:
        offset = (page - 1) * limit
        stmt = select(InquiryModel)
        if company_ids is not None:
            ids = [str(x) for x in company_ids if x is not None]
            if not ids:
                return []
            stmt = stmt.where(InquiryModel.company_id.in_(ids))
        stmt = stmt.order_by(InquiryModel.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]

    async def count_sent(self, company_ids=None) -> int:
        stmt = select(func.count()).select_from(InquiryModel)
        if company_ids is not None:
            ids = [str(x) for x in company_ids if x is not None]
            if not ids:
                return 0
            stmt = stmt.where(InquiryModel.company_id.in_(ids))
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def list_received(self, page: int = 1, limit: int = 20, seller_company_ids=None) -> list:
        """Dopyty na listingy, ktoré patria mojim firmám."""
        offset = (page - 1) * limit
        stmt = (
            select(InquiryModel)
            .join(ListingsModel, InquiryModel.listing_id == ListingsModel.id)
        )
        if seller_company_ids is not None:
            ids = [str(x) for x in seller_company_ids if x is not None]
            if not ids:
                return []
            stmt = stmt.where(ListingsModel.company_id.in_(ids))
        stmt = stmt.order_by(InquiryModel.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]

    async def count_received(self, seller_company_ids=None) -> int:
        stmt = (
            select(func.count())
            .select_from(InquiryModel)
            .join(ListingsModel, InquiryModel.listing_id == ListingsModel.id)
        )
        if seller_company_ids is not None:
            ids = [str(x) for x in seller_company_ids if x is not None]
            if not ids:
                return 0
            stmt = stmt.where(ListingsModel.company_id.in_(ids))
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def create(self, entity: InquiryEntity) -> InquiryEntity:
        model = to_model(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return to_domain(model)

    async def update(self, entity: InquiryEntity) -> InquiryEntity:
        model = await self.session.get(InquiryModel, entity.id)
        if model is None:
            raise ValueError("Entity not found")
        model.listing_id = entity.listing_id
        model.company_id = entity.company_id
        model.message = entity.message
        model.contact_email = entity.contact_email
        model.contact_phone = entity.contact_phone
        model.status = entity.status.value
        model.updated_at = entity.updated_at
        model.updated_by_user_id = entity.updated_by_user_id
        await self.session.commit()
        await self.session.refresh(model)
        return to_domain(model)

    async def delete(self, id: str) -> None:
        await self.session.execute(sql_delete(InquiryModel).where(InquiryModel.id == id))
        await self.session.commit()
