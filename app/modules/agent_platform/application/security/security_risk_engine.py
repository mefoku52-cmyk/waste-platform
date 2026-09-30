"""Security risk engine contract."""

from abc import ABC, abstractmethod

from ...domain.security.security_risk import SecurityRisk, SecurityRiskLevel
from ...domain.security.security_signal import SecuritySignal


class SecurityRiskEngine(ABC):
    @abstractmethod
    async def evaluate(self, signal: SecuritySignal) -> SecurityRisk:
        raise NotImplementedError


class DefaultSecurityRiskEngine(SecurityRiskEngine):
    """Konkretna implementacia SecurityRiskEngine.

    Mapuje confidence -> uroven rizika. Cisto deterministicke.
    """

    async def evaluate(self, signal: SecuritySignal) -> SecurityRisk:
        confidence = float(signal.confidence)
        if confidence >= 0.90:
            level = SecurityRiskLevel.CRITICAL
        elif confidence >= 0.70:
            level = SecurityRiskLevel.HIGH
        elif confidence >= 0.40:
            level = SecurityRiskLevel.MEDIUM
        elif confidence > 0.0:
            level = SecurityRiskLevel.LOW
        else:
            level = SecurityRiskLevel.NONE
        return SecurityRisk(level=level, score=confidence)
