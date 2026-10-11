"""AI message domain entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

_ALLOWED_ROLES = frozenset({"user", "assistant", "tool", "system", "summary"})


@dataclass(frozen=True, slots=True)
class AiMessage:
    id: str
    conversation_id: str
    role: str
    content: str
    tool_calls: str | None
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id is required")
        if not self.conversation_id.strip():
            raise ValueError("conversation_id is required")
        if self.role not in _ALLOWED_ROLES:
            raise ValueError(f"Unsupported role: {self.role}")
        if not self.content.strip() and not self.tool_calls:
            raise ValueError("content or tool_calls is required")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
