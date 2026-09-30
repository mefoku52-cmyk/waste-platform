from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.timezone import to_naive_utc

"""Alert persistence contract."""

from abc import ABC, abstractmethod

from ...domain.alerts.alert_record import AlertRecord
from ...domain.alerts.alert_status import AlertStatus


class AlertRepository(ABC):
    @abstractmethod
    async def create(self, alert: AlertRecord) -> AlertRecord:
        raise NotImplementedError

    @abstractmethod
    async def get(self, alert_id: str) -> AlertRecord | None:
        raise NotImplementedError

    @abstractmethod
    async def update_status(
        self,
        alert_id: str,
        status: AlertStatus,
        assigned_to: str | None = None,
        resolution: str | None = None,
    ) -> AlertRecord:
        raise NotImplementedError


class SqlAlchemyAlertRepository(AlertRepository):
    """SQLAlchemy implementation of alert persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, alert: AlertRecord) -> AlertRecord:
        import json

        from app.modules.agent_platform.infrastructure.models import AlertRecordModel

        m = AlertRecordModel(
            alert_id=alert.alert_id,
            category=alert.category,
            severity=alert.severity.value,
            source=alert.source,
            actor_id=alert.actor_id,
            target=alert.target,
            event=alert.event,
            evidence=json.dumps(alert.evidence, default=str) if alert.evidence else None,
            status=alert.status.value,
            created_at=to_naive_utc(alert.created_at),
            assigned_to=alert.assigned_to,
            resolution=alert.resolution,
        )
        self._session.add(m)
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return self._to_domain(m)

    async def get(self, alert_id: str) -> AlertRecord | None:
        from app.modules.agent_platform.infrastructure.models import AlertRecordModel

        m = await self._session.get(AlertRecordModel, alert_id)
        return self._to_domain(m) if m else None

    async def update_status(
        self,
        alert_id: str,
        status: AlertStatus,
        assigned_to: str | None = None,
        resolution: str | None = None,
    ) -> AlertRecord:
        from app.modules.agent_platform.infrastructure.models import AlertRecordModel

        m = await self._session.get(AlertRecordModel, alert_id)
        if m is None:
            raise ValueError(f"Alert {alert_id} not found")
        m.status = status.value
        if assigned_to is not None:
            m.assigned_to = assigned_to
        if resolution is not None:
            m.resolution = resolution
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return self._to_domain(m)

    @staticmethod
    def _to_domain(m) -> AlertRecord:
        import json

        from app.modules.agent_platform.domain.alerts.alert_severity import AlertSeverity
        from app.modules.agent_platform.domain.alerts.alert_status import AlertStatus as _AS

        evidence: dict = {}
        if m.evidence:
            try:
                evidence = json.loads(m.evidence)
            except (TypeError, ValueError):
                evidence = {}
        return AlertRecord(
            alert_id=m.alert_id,
            category=m.category,
            severity=AlertSeverity(m.severity),
            source=m.source,
            actor_id=m.actor_id,
            target=m.target,
            event=m.event,
            evidence=evidence,
            created_at=m.created_at,
            status=_AS(m.status),
            assigned_to=m.assigned_to,
            resolution=m.resolution,
        )
