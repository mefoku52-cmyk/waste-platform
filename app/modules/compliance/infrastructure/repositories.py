"""compliance repository implementations."""

from typing import List, Optional

from sqlalchemy import delete as sql_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.entities import ComplianceRecordEntity
from ..domain.repositories import ComplianceRecordRepository
from .mappers import to_domain, to_model
from .models import ComplianceRecordModel


class ComplianceRecordRepositoryImpl(ComplianceRecordRepository):
    """ComplianceRecord repository implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: str) -> Optional[ComplianceRecordEntity]:
        result = await self.session.execute(select(ComplianceRecordModel).where(ComplianceRecordModel.id == id))
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def list_by_company_ids(self, company_ids, page: int = 1, limit: int = 20):
        if not company_ids:
            return []
        offset = (page - 1) * limit
        result = await self.session.execute(
            select(ComplianceRecordModel)
            .where(ComplianceRecordModel.company_id.in_(list(company_ids)))
            .order_by(ComplianceRecordModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return [to_domain(m) for m in result.scalars().all()]

    async def count_by_company_ids(self, company_ids) -> int:
        if not company_ids:
            return 0
        result = await self.session.execute(
            select(func.count()).select_from(ComplianceRecordModel).where(
                ComplianceRecordModel.company_id.in_(list(company_ids))
            )
        )
        return int(result.scalar_one())

    async def list_all(self, page: int = 1, limit: int = 20) -> List[ComplianceRecordEntity]:
        offset = (page - 1) * limit
        result = await self.session.execute(select(ComplianceRecordModel).order_by(ComplianceRecordModel.created_at.desc()).offset(offset).limit(limit))
        models = result.scalars().all()
        return [to_domain(m) for m in models]

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(ComplianceRecordModel))
        return int(result.scalar_one())

    async def create(self, entity: ComplianceRecordEntity) -> ComplianceRecordEntity:
        model = to_model(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return to_domain(model)

    async def update(self, entity: ComplianceRecordEntity) -> ComplianceRecordEntity:
        model = await self.session.get(ComplianceRecordModel, entity.id)
        if model is None:
            raise ValueError("Entity not found")
        model.company_id = entity.company_id
        model.regulation_type = entity.regulation_type
        model.document_ref = entity.document_ref
        model.valid_until = entity.valid_until
        model.notes = entity.notes
        model.status = entity.status.value
        model.updated_at = entity.updated_at
        model.updated_by_user_id = entity.updated_by_user_id
        await self.session.commit()
        await self.session.refresh(model)
        return to_domain(model)

    async def delete(self, id: str) -> None:
        await self.session.execute(sql_delete(ComplianceRecordModel).where(ComplianceRecordModel.id == id))
        await self.session.commit()
