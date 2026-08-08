from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.company_memberships.domain.entities import CompanyMembership


class CompanyMembershipRepository(ABC):
    @abstractmethod
    async def add(self, membership: CompanyMembership) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, membership_id: UUID) -> CompanyMembership | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_company_id(self, company_id: UUID, status: str | None = None) -> list[CompanyMembership]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_user_id(self, user_id: UUID) -> list[CompanyMembership]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, membership: CompanyMembership) -> None:
        raise NotImplementedError
