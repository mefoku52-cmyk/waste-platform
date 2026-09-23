"""Audit persistence contract."""

from abc import ABC, abstractmethod

from ...domain.audit.audit_record import AuditRecord


class AuditStore(ABC):
    """Persistence boundary for Agent Platform audit records."""

    @abstractmethod
    async def append(self, record: AuditRecord) -> AuditRecord:
        raise NotImplementedError

    @abstractmethod
    async def get(self, audit_id: str) -> AuditRecord | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_actor(
        self,
        actor_id: str,
    ) -> tuple[AuditRecord, ...]:
        raise NotImplementedError
