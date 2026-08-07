from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.companies.domain.entities import Company


class CompanyRepository(ABC):
    @abstractmethod
    async def add(self, company: Company) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, company_id: UUID) -> Company | None:
        raise NotImplementedError

    @abstractmethod
    async def list(
        self,
        *,
        status: str | None,
        company_type: str | None,
        seller_capability: bool | None,
        buyer_capability: bool | None,
        logistics_capability: bool | None,
        q: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Company], int]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, company: Company) -> None:
        raise NotImplementedError
