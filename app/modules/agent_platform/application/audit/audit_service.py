"""Audit service contract."""

from abc import ABC, abstractmethod

from ...domain.audit.audit_record import AuditRecord


class AuditService(ABC):
    @abstractmethod
    async def record(self, record: AuditRecord) -> AuditRecord:
        raise NotImplementedError


class DefaultAuditService(AuditService):
    """Konkretna implementacia AuditService."""

    def __init__(self, *, store) -> None:
        self._store = store

    async def record(self, record: AuditRecord) -> AuditRecord:
        return await self._store.append(record)
