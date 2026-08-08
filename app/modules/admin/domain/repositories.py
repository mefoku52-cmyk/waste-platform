"""admin domain repositories."""

from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import AdminAuditEntryEntity


class AdminAuditEntryRepository(ABC):
    """AdminAuditEntry repository interface."""

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[AdminAuditEntryEntity]:
        pass

    @abstractmethod
    async def list_all(self, page: int = 1, limit: int = 20) -> List[AdminAuditEntryEntity]:
        pass

    @abstractmethod
    async def count_all(self) -> int:
        pass

    @abstractmethod
    async def create(self, entity: AdminAuditEntryEntity) -> AdminAuditEntryEntity:
        pass

    @abstractmethod
    async def update(self, entity: AdminAuditEntryEntity) -> AdminAuditEntryEntity:
        pass

    @abstractmethod
    async def delete(self, id: str) -> None:
        pass
