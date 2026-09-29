"""Alert service contract."""

from abc import ABC, abstractmethod

from ...domain.alerts.alert_record import AlertRecord


class AlertService(ABC):
    @abstractmethod
    async def create(self, alert: AlertRecord) -> AlertRecord:
        raise NotImplementedError

    @abstractmethod
    async def acknowledge(self, alert_id: str, actor_id: str) -> AlertRecord:
        raise NotImplementedError

    @abstractmethod
    async def resolve(
        self,
        alert_id: str,
        actor_id: str,
        resolution: str,
    ) -> AlertRecord:
        raise NotImplementedError


class DefaultAlertService(AlertService):
    """Konkretna implementacia AlertService."""

    def __init__(self, *, repository) -> None:
        self._repository = repository

    async def create(self, alert: AlertRecord) -> AlertRecord:
        return await self._repository.create(alert)

    async def acknowledge(self, alert_id: str, actor_id: str) -> AlertRecord:
        from app.modules.agent_platform.domain.alerts.alert_status import AlertStatus

        return await self._repository.update_status(
            alert_id,
            AlertStatus.ACKNOWLEDGED,
            assigned_to=actor_id,
        )

    async def resolve(
        self,
        alert_id: str,
        actor_id: str,
        resolution: str,
    ) -> AlertRecord:
        from app.modules.agent_platform.domain.alerts.alert_status import AlertStatus

        return await self._repository.update_status(
            alert_id,
            AlertStatus.RESOLVED,
            assigned_to=actor_id,
            resolution=resolution,
        )
