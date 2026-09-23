"""Approval decision."""

from dataclasses import dataclass
from datetime import datetime

from .approval_status import ApprovalStatus


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    approval_id: str
    status: ApprovalStatus
    decided_by: str | None
    decided_at: datetime | None
    reason: str

    def __post_init__(self) -> None:
        if not self.approval_id.strip():
            raise ValueError("approval_id is required")
        if not self.reason.strip():
            raise ValueError("reason is required")

        if self.decided_at is not None and self.decided_at.tzinfo is None:
            raise ValueError("decided_at must be timezone-aware")
