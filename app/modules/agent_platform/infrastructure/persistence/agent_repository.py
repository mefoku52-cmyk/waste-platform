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


class InMemoryAgentRepository(AgentRepository):
    """Jednoducha in-memory implementacia AgentRepository.

    Session sa drzi v dict-e pocas zivota procesu. Staci pre
    jednoduche pouzitie. V buducnosti nahradi DB verziou.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, AgentSession] = {}

    async def save_session(self, session: AgentSession) -> AgentSession:
        self._sessions[session.session_id] = session
        return session

    async def get_session(self, session_id: str) -> AgentSession | None:
        return self._sessions.get(session_id)
