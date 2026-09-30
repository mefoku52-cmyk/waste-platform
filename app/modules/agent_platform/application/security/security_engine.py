"""Security decision engine contract."""

from abc import ABC, abstractmethod

from ...domain.security.security_decision import SecurityDecision
from ...domain.security.security_observation import SecurityObservation


class SecurityEngine(ABC):
    @abstractmethod
    async def evaluate(self, observation: SecurityObservation) -> SecurityDecision:
        raise NotImplementedError


_PATTERN_DECISION = {
    "prompt_injection": "alert",
    "manipulation": "monitor",
    "social_engineering": "alert",
    "coercion": "alert",
    "data_leakage": "block",
    "permission_escalation": "block",
    "unusual_activity": "monitor",
    "repeated_behavior": "alert",
    "tool_abuse": "alert",
    "auth_anomaly": "alert",
}


class DefaultSecurityEngine(SecurityEngine):
    """Konkretna implementacia SecurityEngine."""

    async def evaluate(self, observation: SecurityObservation) -> SecurityDecision:
        pattern_value = (
            observation.pattern.value
            if hasattr(observation.pattern, "value")
            else str(observation.pattern)
        )
        decision_value = _PATTERN_DECISION.get(pattern_value, "monitor")
        return SecurityDecision(decision_value)
