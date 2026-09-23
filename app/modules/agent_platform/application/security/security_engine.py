"""Security decision engine contract."""

from abc import ABC, abstractmethod

from ...domain.security.security_decision import SecurityDecision
from ...domain.security.security_observation import SecurityObservation


class SecurityEngine(ABC):
    @abstractmethod
    async def evaluate(self, observation: SecurityObservation) -> SecurityDecision:
        raise NotImplementedError
