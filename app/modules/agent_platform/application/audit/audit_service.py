"""Audit service contract."""

from abc import ABC, abstractmethod

from ...domain.audit.audit_record import AuditRecord


class AuditService(ABC):
    @abstractmethod
    async def record(self, record: AuditRecord) -> AuditRecord:
        raise NotImplementedError
