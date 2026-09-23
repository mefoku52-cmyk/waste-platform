"""Policy evaluator contract."""

from abc import ABC, abstractmethod

from ...domain.policy.policy_context import PolicyContext
from ...domain.policy.policy_decision import PolicyDecision


class PolicyEvaluator(ABC):
    @abstractmethod
    async def evaluate(self, context: PolicyContext) -> PolicyDecision:
        raise NotImplementedError
