"""Alert record."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .alert_severity import AlertSeverity
from .alert_status import AlertStatus


@dataclass(frozen=True, slots=True)
class AlertRecord:
    """Security/system/AI alert."""

    alert_id: str
    category: str
    severity: AlertSeverity
    source: str
    actor_id: str | None
    target: str | None
    event: str
    evidence: dict[str, Any]
    created_at: datetime
    status: AlertStatus = AlertStatus.OPEN
    assigned_to: str | None = None
    resolution: str | None = None

    def __post_init__(self) -> None:
        if not self.alert_id.strip():
            raise ValueError("alert_id is required")
        if not self.category.strip():
            raise ValueError("category is required")
        if not self.source.strip():
            raise ValueError("source is required")
        if not self.event.strip():
            raise ValueError("event is required")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
