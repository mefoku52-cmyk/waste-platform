"""Security alert service contract."""

from abc import ABC, abstractmethod

from ...domain.alerts.alert_record import AlertRecord


class SecurityAlertService(ABC):
    @abstractmethod
    async def create(self, alert: AlertRecord) -> AlertRecord:
        raise NotImplementedError
