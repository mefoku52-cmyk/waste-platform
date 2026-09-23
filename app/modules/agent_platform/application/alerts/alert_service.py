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
