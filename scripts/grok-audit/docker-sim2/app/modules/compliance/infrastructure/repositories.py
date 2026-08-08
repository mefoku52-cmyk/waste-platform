"""compliance repository implementations."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..domain.entities import ComplianceEntity
from ..domain.repositories import ComplianceRepository
from .models import ComplianceModel


class ComplianceRepositoryImpl(ComplianceRepository):
    """Compliance repository implementation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, id: str) -> Optional[ComplianceEntity]:
        result = await self.session.execute(
            select(ComplianceModel).where(ComplianceModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model:
            return ComplianceEntity(id=str(model.id))
        return None
    
    async def list_all(self, page: int = 1, limit: int = 20) -> List[ComplianceEntity]:
        offset = (page - 1) * limit
        result = await self.session.execute(
            select(ComplianceModel).offset(offset).limit(limit)
        )
        models = result.scalars().all()
        return [ComplianceEntity(id=str(m.id)) for m in models]
    
    async def create(self, entity: ComplianceEntity) -> ComplianceEntity:
        model = ComplianceModel()
        self.session.add(model)
        await self.session.flush()
        return ComplianceEntity(id=str(model.id))
    
    async def update(self, entity: ComplianceEntity) -> ComplianceEntity:
        result = await self.session.execute(
            select(ComplianceModel).where(ComplianceModel.id == entity.id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.flush()
            return ComplianceEntity(id=str(model.id))
        raise ValueError("Entity not found")
    
    async def delete(self, id: str) -> None:
        await self.session.execute(
            select(ComplianceModel).where(ComplianceModel.id == id)
        )
        await self.session.flush()
