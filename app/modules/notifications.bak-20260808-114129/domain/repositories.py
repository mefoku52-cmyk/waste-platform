"""notifications domain repositories."""

from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import NotificationsEntity


class NotificationsRepository(ABC):
    """Notifications repository interface."""
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[NotificationsEntity]:
        pass
    
    @abstractmethod
    async def list_all(self, page: int = 1, limit: int = 20) -> List[NotificationsEntity]:
        pass
    
    @abstractmethod
    async def create(self, entity: NotificationsEntity) -> NotificationsEntity:
        pass
    
    @abstractmethod
    async def update(self, entity: NotificationsEntity) -> NotificationsEntity:
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> None:
        pass
