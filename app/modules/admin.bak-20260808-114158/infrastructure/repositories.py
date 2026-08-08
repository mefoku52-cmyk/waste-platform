"""admin repository implementations."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.entities import AdminEntity
from ..domain.repositories import AdminRepository
from .models import AdminModel


class AdminRepositoryImpl(AdminRepository):
    """Admin repository implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _to_entity(model: AdminModel) -> AdminEntity:
        return AdminEntity(
            id=str(model.id),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, id: str) -> Optional[AdminEntity]:
        result = await self.session.execute(
            select(AdminModel).where(AdminModel.id == id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_all(self, page: int = 1, limit: int = 20) -> List[AdminEntity]:
        offset = (page - 1) * limit
        result = await self.session.execute(
            select(AdminModel).offset(offset).limit(limit)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def create(self, entity: AdminEntity) -> AdminEntity:
        raise NotImplementedError("Admin creation is not implemented")

    async def update(self, entity: AdminEntity) -> AdminEntity:
        raise NotImplementedError("Admin update is not implemented")

    async def delete(self, id: str) -> None:
        raise NotImplementedError("Admin deletion is not implemented")
