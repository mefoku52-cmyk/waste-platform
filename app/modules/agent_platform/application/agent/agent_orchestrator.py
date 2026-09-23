"""Agent orchestration contract.

This file intentionally contains the orchestration boundary only.
Provider/model implementation will be added after the contracts are verified.
"""

from abc import ABC, abstractmethod

from .agent_context import AgentContext
from .agent_response import AgentResponse


class AgentOrchestrator(ABC):
    """Coordinates context, model reasoning, tools and policy.

    It does not own authentication or authorization.
    """

    @abstractmethod
    async def respond(self, context: AgentContext) -> AgentResponse:
        """Generate a controlled agent response."""
        raise NotImplementedError
