"""admin application services."""

from typing import List, Optional

from ..domain.entities import AdminEntity
from ..domain.repositories import AdminRepository


class AdminService:
    """Read-only admin service."""

    def __init__(self, repository: AdminRepository):
        self.repository = repository

    async def get_by_id(self, id: str) -> Optional[AdminEntity]:
        return await self.repository.get_by_id(id)

    async def list_all(self, page: int = 1, limit: int = 20) -> List[AdminEntity]:
        return await self.repository.list_all(page, limit)
