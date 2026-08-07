"""notifications application services."""

from typing import List, Optional

from ..domain.entities import NotificationsEntity
from ..domain.repositories import NotificationsRepository


class NotificationsService:
    """Notifications service."""
    
    def __init__(self, repository: NotificationsRepository):
        self.repository = repository
    
    async def get_by_id(self, id: str) -> Optional[NotificationsEntity]:
        return await self.repository.get_by_id(id)
    
    async def list_all(self, page: int = 1, limit: int = 20) -> List[NotificationsEntity]:
        return await self.repository.list_all(page, limit)
