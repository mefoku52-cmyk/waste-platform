"""Security signal service contract."""

import contextlib
from abc import ABC, abstractmethod

from ...domain.security.security_observation import SecurityObservation
from ...domain.security.security_signal import SecuritySignal


class SecuritySignalService(ABC):
    @abstractmethod
    async def observe(self, observation: SecurityObservation) -> SecuritySignal:
        raise NotImplementedError


class DefaultSecuritySignalService(SecuritySignalService):
    """Konkretna implementacia SecuritySignalService.

    Z observation vytvori signal. Confidence sa odvodi od vzoru.
    Signal sa ulozi do security_event_store, ak je k dispozicii.
    """

    _PATTERN_CONFIDENCE = {
        "prompt_injection": 0.90,
        "data_leakage": 0.95,
        "permission_escalation": 0.85,
        "social_engineering": 0.75,
        "coercion": 0.75,
        "tool_abuse": 0.70,
        "manipulation": 0.60,
        "repeated_behavior": 0.55,
        "auth_anomaly": 0.65,
        "unusual_activity": 0.40,
    }

    def __init__(self, *, store=None) -> None:
        self._store = store

    async def observe(self, observation: SecurityObservation) -> SecuritySignal:
        from datetime import UTC, datetime
        from uuid import uuid4

        pattern_value = (
            observation.pattern.value
            if hasattr(observation.pattern, "value")
            else str(observation.pattern)
        )
        confidence = self._PATTERN_CONFIDENCE.get(pattern_value, 0.30)
        signal = SecuritySignal(
            signal_id=str(uuid4()),
            pattern=observation.pattern,
            confidence=confidence,
            source_observation_id=observation.observation_id,
            created_at=datetime.now(UTC),
        )
        if self._store is not None:
            with contextlib.suppress(Exception):
                await self._store.store_signal(signal)
        return signal
