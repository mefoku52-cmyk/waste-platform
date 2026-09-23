"""Agent response."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AgentResponse:
    session_id: str
    text: str
    tool_calls: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    citations: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    requires_approval: bool = False
    approval_id: str | None = None
