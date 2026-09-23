"""Security event storage contract."""

from abc import ABC, abstractmethod

from ...domain.security.security_observation import SecurityObservation
from ...domain.security.security_signal import SecuritySignal


class SecurityEventStore(ABC):
    """Storage boundary for security observations/signals."""

    @abstractmethod
    async def store_observation(
        self,
        observation: SecurityObservation,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def store_signal(
        self,
        signal: SecuritySignal,
    ) -> None:
        raise NotImplementedError
