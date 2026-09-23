"""Agent Platform audit record."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .audit_action import AuditAction
from .audit_subject import AuditSubject


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """Audit event produced by controlled platform operations."""

    audit_id: str
    actor_id: str | None
    actor_type: str
    action: AuditAction
    subject: AuditSubject | None
    occurred_at: datetime
    success: bool
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.audit_id.strip():
            raise ValueError("audit_id is required")
        if not self.actor_type.strip():
            raise ValueError("actor_type is required")
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
