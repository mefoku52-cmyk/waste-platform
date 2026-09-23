"""Agent persistence contract."""

from abc import ABC, abstractmethod

from ...application.agent.agent_session import AgentSession


class AgentRepository(ABC):
    @abstractmethod
    async def save_session(self, session: AgentSession) -> AgentSession:
        raise NotImplementedError

    @abstractmethod
    async def get_session(self, session_id: str) -> AgentSession | None:
        raise NotImplementedError
