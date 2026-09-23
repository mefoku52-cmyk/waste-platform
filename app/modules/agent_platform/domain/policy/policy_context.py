"""Policy evaluation context."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PolicyContext:
    """Context supplied to policy evaluation."""

    actor_id: str | None
    actor_type: str
    agent_id: str | None
    action: str
    target: str | None
    tool_name: str | None
    risk_level: str | None
    attributes: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.actor_type.strip():
            raise ValueError("actor_type is required")
        if not self.action.strip():
            raise ValueError("action is required")
