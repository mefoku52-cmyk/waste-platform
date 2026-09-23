"""Agent session application model."""

from dataclasses import dataclass
from datetime import datetime

from ...domain.agent.agent_identity import AgentIdentity
from ...domain.agent.agent_scope import AgentScope
from ...domain.agent.agent_state import AgentState


@dataclass(frozen=True, slots=True)
class AgentSession:
    session_id: str
    identity: AgentIdentity
    scope: AgentScope
    state: AgentState
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.session_id.strip():
            raise ValueError("session_id is required")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
