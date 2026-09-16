from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.infrastructure.models import NotificationModel


class NotificationRepository(ABC):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.model = NotificationModel

    @abstractmethod
    async def get_by_id(self, id: str): ...

    @abstractmethod
    async def list_by_user_id(self, user_id, page: int = 1, limit: int = 20): ...

    @abstractmethod
    async def count_by_user_id(self, user_id) -> int: ...

    @abstractmethod
    async def list_all(self, page: int = 1, limit: int = 20): ...

    @abstractmethod
    async def count_all(self) -> int: ...

    @abstractmethod
    async def create(self, entity): ...

    @abstractmethod
    async def update(self, entity): ...

    @abstractmethod
    async def delete(self, id: str) -> None: ...

    @abstractmethod
    async def count_unread(self, user_id) -> int: ...
