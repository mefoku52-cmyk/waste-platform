"""Platform event."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .event_source import EventSource
from .event_type import PlatformEventType


@dataclass(frozen=True, slots=True)
class PlatformEvent:
    """Immutable event emitted by the Agent Platform."""

    event_id: str
    event_type: PlatformEventType
    source: EventSource
    occurred_at: datetime
    actor_id: str | None = None
    correlation_id: str | None = None
    target: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError("event_id is required")
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
