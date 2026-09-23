"""Security signal service contract."""

from abc import ABC, abstractmethod

from ...domain.security.security_observation import SecurityObservation
from ...domain.security.security_signal import SecuritySignal


class SecuritySignalService(ABC):
    @abstractmethod
    async def observe(self, observation: SecurityObservation) -> SecuritySignal:
        raise NotImplementedError
