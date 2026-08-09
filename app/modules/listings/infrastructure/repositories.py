"""listings repository implementations."""

from typing import List, Optional

from sqlalchemy import delete as sql_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.entities import ListingsEntity
from ..domain.repositories import ListingsRepository
from .mappers import to_domain, to_model
from .models import ListingsModel


class ListingsRepositoryImpl(ListingsRepository):
    """Listings repository implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: str) -> Optional[ListingsEntity]:
        result = await self.session.execute(
            select(ListingsModel).where(ListingsModel.id == id)
        )
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def list_all(self, page: int = 1, limit: int = 20) -> List[ListingsEntity]:
        offset = (page - 1) * limit
        result = await self.session.execute(
            select(ListingsModel).order_by(ListingsModel.created_at.desc()).offset(offset).limit(limit)
        )
        models = result.scalars().all()
        return [to_domain(m) for m in models]

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(ListingsModel))
        return int(result.scalar_one())

    async def create(self, entity: ListingsEntity) -> ListingsEntity:
        model = to_model(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return to_domain(model)

    async def update(self, entity: ListingsEntity) -> ListingsEntity:
        model = await self.session.get(ListingsModel, entity.id)
        if model is None:
            raise ValueError("Entity not found")
        model.title = entity.title
        model.material_type = entity.material_type
        model.quantity = entity.quantity
        model.unit = entity.unit
        model.price = entity.price
        model.currency = entity.currency
        model.condition = entity.condition
        model.location = entity.location
        model.status = entity.status.value
        model.description = entity.description
        model.updated_at = entity.updated_at
        model.updated_by_user_id = entity.updated_by_user_id
        await self.session.commit()
        await self.session.refresh(model)
        return to_domain(model)

    async def delete(self, id: str) -> None:
        await self.session.execute(
            sql_delete(ListingsModel).where(ListingsModel.id == id)
        )
        await self.session.commit()
