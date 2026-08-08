"""admin domain entities."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.admin.domain.enums import AdminAuditEntryStatus
from app.shared.domain.base import AuditFields
from app.shared.domain.exceptions import ValidationDomainError


@dataclass(slots=True)
class AdminAuditEntryEntity(AuditFields):
    """AdminAuditEntry entity."""

    actor_user_id: UUID
    action: str
    target_type: str
    status: AdminAuditEntryStatus = AdminAuditEntryStatus.SUCCESS
    target_id: UUID | None = None
    details: str | None = None

    def validate(self) -> None:
        if not self.action:
            raise ValidationDomainError("AdminAuditEntry action is required")
        if not self.target_type:
            raise ValidationDomainError("AdminAuditEntry target_type is required")
