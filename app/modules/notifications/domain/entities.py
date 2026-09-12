"""notifications domain entities."""

from dataclasses import dataclass
from uuid import UUID

from app.shared.domain.base import AuditFields
from app.shared.domain.exceptions import ValidationDomainError


@dataclass(slots=True)
class NotificationEntity(AuditFields):
    """Notification entity."""

    user_id: UUID
    type: str
    title: str
    message: str
    is_read: bool = False
    related_entity_id: UUID | None = None

    def validate(self) -> None:
        if not self.type:
            raise ValidationDomainError("Notification type is required")
        if not self.title:
            raise ValidationDomainError("Notification title is required")
        if not self.message:
            raise ValidationDomainError("Notification message is required")
