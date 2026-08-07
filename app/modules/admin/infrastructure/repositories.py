"""admin repository implementations."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..domain.entities import AdminEntity
from ..domain.repositories import AdminRepository
from .models import AdminModel


class AdminRepositoryImpl(AdminRepository):
    """Admin repository implementation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, id: str) -> Optional[AdminEntity]:
        result = await self.session.execute(
            select(AdminModel).where(AdminModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model:
            return AdminEntity(id=str(model.id))
        return None
    
    async def list_all(self, page: int = 1, limit: int = 20) -> List[AdminEntity]:
        offset = (page - 1) * limit
        result = await self.session.execute(
            select(AdminModel).offset(offset).limit(limit)
        )
        models = result.scalars().all()
        return [AdminEntity(id=str(m.id)) for m in models]
    
    async def create(self, entity: AdminEntity) -> AdminEntity:
        model = AdminModel()
        self.session.add(model)
        await self.session.flush()
        return AdminEntity(id=str(model.id))
    
    async def update(self, entity: AdminEntity) -> AdminEntity:
        result = await self.session.execute(
            select(AdminModel).where(AdminModel.id == entity.id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.flush()
            return AdminEntity(id=str(model.id))
        raise ValueError("Entity not found")
    
    async def delete(self, id: str) -> None:
        await self.session.execute(
            select(AdminModel).where(AdminModel.id == id)
        )
        await self.session.flush()
