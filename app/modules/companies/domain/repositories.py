from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.infrastructure.models import CompanyModel


class CompanyRepository(ABC):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.model = CompanyModel

    @abstractmethod
    async def add(self, company) -> None: ...

    @abstractmethod
    async def get_by_id(self, company_id): ...

    @abstractmethod
    async def list(
        self,
        *,
        status: str | None = None,
        company_type: str | None = None,
        seller_capability: bool | None = None,
        buyer_capability: bool | None = None,
        logistics_capability: bool | None = None,
        q: str | None = None,
        page: int = 1,
        page_size: int = 20,
        company_ids: list[int] | None = None,
    ): ...

    @abstractmethod
    async def update(self, company) -> None: ...
