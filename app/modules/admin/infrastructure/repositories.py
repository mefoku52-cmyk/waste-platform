"""admin repository implementations."""

from typing import List, Optional

from sqlalchemy import delete as sql_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.entities import AdminAuditEntryEntity
from ..domain.repositories import AdminAuditEntryRepository
from .mappers import to_domain, to_model
from .models import AdminAuditEntryModel


class AdminAuditEntryRepositoryImpl(AdminAuditEntryRepository):
    """AdminAuditEntry repository implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: str) -> Optional[AdminAuditEntryEntity]:
        result = await self.session.execute(select(AdminAuditEntryModel).where(AdminAuditEntryModel.id == id))
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def list_all(self, page: int = 1, limit: int = 20) -> List[AdminAuditEntryEntity]:
        offset = (page - 1) * limit
        result = await self.session.execute(select(AdminAuditEntryModel).order_by(AdminAuditEntryModel.created_at.desc()).offset(offset).limit(limit))
        models = result.scalars().all()
        return [to_domain(m) for m in models]

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(AdminAuditEntryModel))
        return int(result.scalar_one())

    async def create(self, entity: AdminAuditEntryEntity) -> AdminAuditEntryEntity:
        model = to_model(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return to_domain(model)

    async def update(self, entity: AdminAuditEntryEntity) -> AdminAuditEntryEntity:
        model = await self.session.get(AdminAuditEntryModel, entity.id)
        if model is None:
            raise ValueError("Entity not found")
        model.actor_user_id = entity.actor_user_id
        model.action = entity.action
        model.target_type = entity.target_type
        model.target_id = entity.target_id
        model.details = entity.details
        model.status = entity.status.value
        model.updated_at = entity.updated_at
        model.updated_by_user_id = entity.updated_by_user_id
        await self.session.flush()
        await self.session.refresh(model)
        return to_domain(model)

    async def delete(self, id: str) -> None:
        await self.session.execute(sql_delete(AdminAuditEntryModel).where(AdminAuditEntryModel.id == id))
        await self.session.flush()
