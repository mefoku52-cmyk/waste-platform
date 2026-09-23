"""Runtime context passed through the agent pipeline.

This object carries request metadata. It does not grant authority.
Authority is resolved by policy and permission components.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AgentRuntimeContext:
    request_id: str
    actor_id: str
    actor_type: str
    agent_id: str
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
