"""Break-glass emergency access contract."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class BreakGlassRequest:
    """Emergency request requiring explicit human authority."""

    request_id: str
    requested_by: str
    reason: str
    requested_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id is required")
        if not self.requested_by.strip():
            raise ValueError("requested_by is required")
        if not self.reason.strip():
            raise ValueError("reason is required")
        if self.requested_at.tzinfo is None:
            raise ValueError("requested_at must be timezone-aware")
        if self.expires_at.tzinfo is None:
            raise ValueError("expires_at must be timezone-aware")
        if self.expires_at <= self.requested_at:
            raise ValueError("expires_at must be after requested_at")
