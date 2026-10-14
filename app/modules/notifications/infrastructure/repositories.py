"""notifications repository implementations."""

import uuid

from sqlalchemy import delete as sql_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.entities import NotificationEntity
from ..domain.repositories import NotificationRepository
from .mappers import to_domain, to_model
from .models import NotificationModel


def _uuid(value: str | uuid.UUID) -> uuid.UUID:
    """Normalise a str/uuid identifier to ``uuid.UUID``.

    The model binds its id/user_id columns with ``UUID(as_uuid=True)``. SQLite
    (no native UUID support) raises StatementError when a raw string is bound,
    while Postgres accepts it — so every boundary must coerce first (same
    pattern as the agent_platform conversation repository, N2).
    """
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


class NotificationRepositoryImpl(NotificationRepository):
    """Notification repository implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: str) -> NotificationEntity | None:
        result = await self.session.execute(
            select(NotificationModel).where(NotificationModel.id == _uuid(id))
        )
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def list_by_user_id(self, user_id, page: int = 1, limit: int = 20):
        uid = _uuid(user_id)
        offset = (page - 1) * limit
        result = await self.session.execute(
            select(NotificationModel)
            .where(NotificationModel.user_id == uid)
            .order_by(NotificationModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return [to_domain(m) for m in result.scalars().all()]

    async def count_by_user_id(self, user_id) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(NotificationModel)
            .where(NotificationModel.user_id == _uuid(user_id))
        )
        return int(result.scalar_one())

    async def count_unread(self, user_id) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(NotificationModel)
            .where(NotificationModel.user_id == _uuid(user_id))
            .where(NotificationModel.is_read.is_(False))
        )
        return int(result.scalar_one())

    async def list_all(self, page: int = 1, limit: int = 20) -> list[NotificationEntity]:
        offset = (page - 1) * limit
        result = await self.session.execute(
            select(NotificationModel)
            .order_by(NotificationModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
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
        await self.session.execute(
            sql_delete(NotificationModel).where(NotificationModel.id == _uuid(id))
        )
        await self.session.commit()
