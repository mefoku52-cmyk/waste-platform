"""notifications repository implementations."""

from typing import List, Optional

from sqlalchemy import delete as sql_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.entities import NotificationEntity
from ..domain.repositories import NotificationRepository
from .mappers import to_domain, to_model
from .models import NotificationModel


class NotificationRepositoryImpl(NotificationRepository):
    """Notification repository implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: str) -> Optional[NotificationEntity]:
        result = await self.session.execute(select(NotificationModel).where(NotificationModel.id == id))
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def list_all(self, page: int = 1, limit: int = 20) -> List[NotificationEntity]:
        offset = (page - 1) * limit
        result = await self.session.execute(select(NotificationModel).order_by(NotificationModel.created_at.desc()).offset(offset).limit(limit))
        models = result.scalars().all()
        return [to_domain(m) for m in models]

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(NotificationModel))
        return int(result.scalar_one())

    async def create(self, entity: NotificationEntity) -> NotificationEntity:
        model = to_model(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return to_domain(model)

    async def update(self, entity: NotificationEntity) -> NotificationEntity:
        model = await self.session.get(NotificationModel, entity.id)
        if model is None:
            raise ValueError("Entity not found")
        model.user_id = entity.user_id
        model.type = entity.type
        model.title = entity.title
        model.message = entity.message
        model.is_read = entity.is_read
        model.related_entity_id = entity.related_entity_id
        model.updated_at = entity.updated_at
        model.updated_by_user_id = entity.updated_by_user_id
        await self.session.commit()
        await self.session.refresh(model)
        return to_domain(model)

    async def delete(self, id: str) -> None:
        await self.session.execute(sql_delete(NotificationModel).where(NotificationModel.id == id))
        await self.session.commit()
