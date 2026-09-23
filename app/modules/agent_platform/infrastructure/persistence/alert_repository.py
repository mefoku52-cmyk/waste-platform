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
