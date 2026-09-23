"""Tool request."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ToolRequest:
    """A request to invoke a registered tool."""

    request_id: str
    tool_name: str
    actor_id: str
    actor_type: str
    arguments: dict[str, Any]
    reason: str

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id is required")
        if not self.tool_name.strip():
            raise ValueError("tool_name is required")
        if not self.actor_id.strip():
            raise ValueError("actor_id is required")
        if not self.actor_type.strip():
            raise ValueError("actor_type is required")
        if not self.reason.strip():
            raise ValueError("reason is required")
