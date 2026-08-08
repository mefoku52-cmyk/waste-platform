"""compliance domain entities."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.compliance.domain.enums import ComplianceRecordStatus
from app.shared.domain.base import AuditFields
from app.shared.domain.exceptions import ValidationDomainError


@dataclass(slots=True)
class ComplianceRecordEntity(AuditFields):
    """ComplianceRecord entity."""

    company_id: UUID
    regulation_type: str
    status: ComplianceRecordStatus = ComplianceRecordStatus.PENDING
    document_ref: str | None = None
    valid_until: datetime | None = None
    notes: str | None = None

    def validate(self) -> None:
        if not self.regulation_type:
            raise ValidationDomainError("ComplianceRecord regulation_type is required")
