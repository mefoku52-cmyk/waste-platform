"""Agent identity primitives."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AgentIdentity:
    """Stable identity of an AI agent.

    This is not an authentication identity and does not grant permissions.
    Permissions are evaluated separately.
    """

    agent_id: str
    name: str
    version: str

    def __post_init__(self) -> None:
        if not self.agent_id.strip():
            raise ValueError("agent_id is required")
        if not self.name.strip():
            raise ValueError("name is required")
        if not self.version.strip():
            raise ValueError("version is required")
