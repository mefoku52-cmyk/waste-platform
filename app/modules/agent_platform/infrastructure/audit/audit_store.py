from sqlalchemy.ext.asyncio import AsyncSession

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


class SqlAlchemyAuditStore(AuditStore):
    """SQLAlchemy implementation of Agent Platform audit storage.

    Tabulka: agent_audit_records (nie admin_audit_entries - to je ina vec).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, record: AuditRecord) -> AuditRecord:
        import json

        from sqlalchemy import select

        from app.modules.agent_platform.infrastructure.models import (
            AgentAuditRecordModel,
        )

        existing = (
            await self._session.execute(
                select(AgentAuditRecordModel).where(
                    AgentAuditRecordModel.audit_id == record.audit_id
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return record

        m = AgentAuditRecordModel(
            audit_id=record.audit_id,
            actor_id=record.actor_id,
            actor_type=record.actor_type,
            action=record.action.value,
            subject_type=record.subject.subject_type if record.subject else None,
            subject_id=record.subject.subject_id if record.subject else None,
            occurred_at=record.occurred_at,
            success=record.success,
            reason=record.reason,
            details=json.dumps(record.metadata, default=str) if record.metadata else None,
        )
        self._session.add(m)
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return record

    async def get(self, audit_id: str) -> AuditRecord | None:
        from app.modules.agent_platform.infrastructure.models import (
            AgentAuditRecordModel,
        )

        m = await self._session.get(AgentAuditRecordModel, audit_id)
        return self._to_domain(m) if m else None

    async def list_by_actor(self, actor_id: str) -> tuple[AuditRecord, ...]:
        from sqlalchemy import select

        from app.modules.agent_platform.infrastructure.models import (
            AgentAuditRecordModel,
        )

        rows = (
            (
                await self._session.execute(
                    select(AgentAuditRecordModel)
                    .where(AgentAuditRecordModel.actor_id == actor_id)
                    .order_by(AgentAuditRecordModel.occurred_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return tuple(self._to_domain(m) for m in rows)

    @staticmethod
    def _to_domain(m) -> AuditRecord:
        import json

        from app.modules.agent_platform.domain.audit.audit_action import AuditAction
        from app.modules.agent_platform.domain.audit.audit_subject import AuditSubject

        subject = None
        if m.subject_type and m.subject_id:
            subject = AuditSubject(
                subject_type=m.subject_type,
                subject_id=m.subject_id,
            )
        metadata: dict = {}
        if m.details:
            try:
                metadata = json.loads(m.details)
            except (TypeError, ValueError):
                metadata = {}
        return AuditRecord(
            audit_id=m.audit_id,
            actor_id=m.actor_id,
            actor_type=m.actor_type,
            action=AuditAction(m.action),
            subject=subject,
            occurred_at=m.occurred_at,
            success=bool(m.success),
            reason=m.reason,
            metadata=metadata,
        )
