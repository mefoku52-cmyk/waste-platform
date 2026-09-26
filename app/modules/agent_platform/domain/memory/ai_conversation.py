"""AI conversation domain entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AiConversation:
    id: str
    session_id: str
    user_id: str
    company_id: str | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id is required")
        if not self.session_id.strip():
            raise ValueError("session_id is required")
        if not self.user_id.strip():
            raise ValueError("user_id is required")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if self.updated_at.tzinfo is None:
            raise ValueError("updated_at must be timezone-aware")
