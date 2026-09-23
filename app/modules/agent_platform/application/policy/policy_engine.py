"""Policy engine facade."""

from abc import ABC, abstractmethod

from ...domain.policy.policy_context import PolicyContext
from ...domain.policy.policy_decision import PolicyDecision


class PolicyEngine(ABC):
    @abstractmethod
    async def decide(self, context: PolicyContext) -> PolicyDecision:
        raise NotImplementedError
