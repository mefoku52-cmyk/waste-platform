"""analytics domain repositories."""

from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import AnalyticsEventEntity


class AnalyticsEventRepository(ABC):
    """AnalyticsEvent repository interface."""

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[AnalyticsEventEntity]:
        pass

    @abstractmethod
    async def list_all(self, page: int = 1, limit: int = 20) -> List[AnalyticsEventEntity]:
        pass

    @abstractmethod
    async def count_all(self) -> int:
        pass

    @abstractmethod
    async def create(self, entity: AnalyticsEventEntity) -> AnalyticsEventEntity:
        pass

    @abstractmethod
    async def update(self, entity: AnalyticsEventEntity) -> AnalyticsEventEntity:
        pass

    @abstractmethod
    async def delete(self, id: str) -> None:
        pass
