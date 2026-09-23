"""Approval request."""

from dataclasses import dataclass
from datetime import datetime

from .approval_status import ApprovalStatus


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    """Human approval request for a sensitive operation."""

    approval_id: str
    requested_by: str
    requested_by_type: str
    action: str
    target: str | None
    reason: str
    risk_level: str
    created_at: datetime
    expires_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING

    def __post_init__(self) -> None:
        if not self.approval_id.strip():
            raise ValueError("approval_id is required")
        if not self.requested_by.strip():
            raise ValueError("requested_by is required")
        if not self.requested_by_type.strip():
            raise ValueError("requested_by_type is required")
        if not self.action.strip():
            raise ValueError("action is required")
        if not self.reason.strip():
            raise ValueError("reason is required")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if self.expires_at.tzinfo is None:
            raise ValueError("expires_at must be timezone-aware")
        if self.expires_at <= self.created_at:
            raise ValueError("expires_at must be after created_at")
