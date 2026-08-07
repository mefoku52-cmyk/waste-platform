from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.auth.domain.entities import RefreshSession


class RefreshSessionRepository(ABC):
    @abstractmethod
    async def add(self, session: RefreshSession) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_jti(self, jti: str) -> RefreshSession | None:
        raise NotImplementedError

    @abstractmethod
    async def get_active_by_user_id(self, user_id: UUID) -> list[RefreshSession]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, session: RefreshSession) -> None:
        raise NotImplementedError

    @abstractmethod
    async def revoke_family(self, family_id: str, revoked_at) -> None:
        raise NotImplementedError
