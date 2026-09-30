"""Security alert service contract."""

from abc import ABC, abstractmethod

from ...domain.alerts.alert_record import AlertRecord


class SecurityAlertService(ABC):
    @abstractmethod
    async def create(self, alert: AlertRecord) -> AlertRecord:
        raise NotImplementedError


class DefaultSecurityAlertService(SecurityAlertService):
    """Konkretna implementacia SecurityAlertService.

    Z observation vytvori alert. Pouzije alert_service (ak je dany).
    """

    _SEVERITY_BY_PATTERN = {
        "data_leakage": "critical",
        "permission_escalation": "critical",
        "prompt_injection": "high",
        "social_engineering": "high",
        "coercion": "high",
        "tool_abuse": "medium",
        "manipulation": "medium",
        "auth_anomaly": "medium",
        "repeated_behavior": "low",
        "unusual_activity": "low",
    }

    def __init__(self, *, alert_service=None) -> None:
        self._alert_service = alert_service

    async def create(self, alert: AlertRecord) -> AlertRecord:
        if self._alert_service is None:
            return alert
        return await self._alert_service.create(alert)

    @classmethod
    def severity_for(cls, pattern_value: str) -> str:
        return cls._SEVERITY_BY_PATTERN.get(pattern_value, "low")
