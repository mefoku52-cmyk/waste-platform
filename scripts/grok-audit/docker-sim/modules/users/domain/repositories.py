from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.users.domain.entities import User


class UserRepository(ABC):
    @abstractmethod
    async def add(self, user: User) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def list(self, *, status: str | None, company_id: UUID | None, q: str | None, page: int, page_size: int) -> tuple[list[User], int]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, user: User) -> None:
        raise NotImplementedError
