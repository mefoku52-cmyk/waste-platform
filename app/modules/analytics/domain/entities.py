"""analytics domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.shared.domain.base import AuditFields
from app.shared.domain.exceptions import ValidationDomainError


@dataclass(slots=True)
class AnalyticsEventEntity(AuditFields):
    """AnalyticsEvent entity."""

    event_type: str
    entity_type: str
    entity_id: UUID | None = None
    company_id: UUID | None = None
    event_metadata: str | None = None
    recorded_at: datetime = field(default_factory=datetime.utcnow)

    def validate(self) -> None:
        if not self.event_type:
            raise ValidationDomainError("AnalyticsEvent event_type is required")
        if not self.entity_type:
            raise ValidationDomainError("AnalyticsEvent entity_type is required")
