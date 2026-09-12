"""notifications application services."""

from app.shared.domain.exceptions import NotFoundDomainError

from ..domain.entities import NotificationEntity
from ..domain.repositories import NotificationRepository


class NotificationService:
    """Notification service."""

    def __init__(self, repository: NotificationRepository):
        self.repository = repository

    async def get_by_id(self, id: str) -> NotificationEntity | None:
        return await self.repository.get_by_id(id)

    async def list_all(self, page: int = 1, limit: int = 20) -> list[NotificationEntity]:
        return await self.repository.list_all(page, limit)

    async def list_by_user_id(self, user_id, page: int = 1, limit: int = 20):
        return await self.repository.list_by_user_id(user_id, page, limit)

    async def count_by_user_id(self, user_id) -> int:
        return await self.repository.count_by_user_id(user_id)

    async def count_all(self) -> int:
        return await self.repository.count_all()

    async def create(self, entity: NotificationEntity) -> NotificationEntity:
        entity.validate()
        return await self.repository.create(entity)

    async def mark_read(self, id: str) -> NotificationEntity:
        existing = await self.repository.get_by_id(id)
        if existing is None:
            raise NotFoundDomainError(f"Notification {id} not found")
        existing.is_read = True
        return await self.repository.update(existing)

    async def mark_unread(self, id: str) -> NotificationEntity:
        existing = await self.repository.get_by_id(id)
        if existing is None:
            raise NotFoundDomainError(f"Notification {id} not found")
        existing.is_read = False
        return await self.repository.update(existing)

    async def delete(self, id: str) -> None:
        existing = await self.repository.get_by_id(id)
        if existing is None:
            raise NotFoundDomainError(f"Notification {id} not found")
        await self.repository.delete(id)
