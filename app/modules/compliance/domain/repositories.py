"""compliance domain repositories."""

from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import ComplianceRecordEntity


class ComplianceRecordRepository(ABC):
    """ComplianceRecord repository interface."""

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[ComplianceRecordEntity]:
        pass

    @abstractmethod
    async def list_all(self, page: int = 1, limit: int = 20) -> List[ComplianceRecordEntity]:
        pass

    @abstractmethod
    async def count_all(self) -> int:
        pass

    @abstractmethod
    async def create(self, entity: ComplianceRecordEntity) -> ComplianceRecordEntity:
        pass

    @abstractmethod
    async def update(self, entity: ComplianceRecordEntity) -> ComplianceRecordEntity:
        pass

    @abstractmethod
    async def delete(self, id: str) -> None:
        pass
