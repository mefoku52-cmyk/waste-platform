"""compliance application services."""

from typing import List, Optional

from ..domain.entities import ComplianceEntity
from ..domain.repositories import ComplianceRepository


class ComplianceService:
    """Compliance service."""
    
    def __init__(self, repository: ComplianceRepository):
        self.repository = repository
    
    async def get_by_id(self, id: str) -> Optional[ComplianceEntity]:
        return await self.repository.get_by_id(id)
    
    async def list_all(self, page: int = 1, limit: int = 20) -> List[ComplianceEntity]:
        return await self.repository.list_all(page, limit)
