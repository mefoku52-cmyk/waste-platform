"""Security risk engine contract."""

from abc import ABC, abstractmethod

from ...domain.security.security_risk import SecurityRisk
from ...domain.security.security_signal import SecuritySignal


class SecurityRiskEngine(ABC):
    @abstractmethod
    async def evaluate(self, signal: SecuritySignal) -> SecurityRisk:
        raise NotImplementedError
