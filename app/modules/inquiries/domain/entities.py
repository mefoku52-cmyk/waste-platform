"""inquiries domain entities."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.inquiries.domain.enums import InquiryStatus
from app.shared.domain.base import AuditFields
from app.shared.domain.exceptions import ValidationDomainError


@dataclass(slots=True)
class InquiryEntity(AuditFields):
    """Inquiry entity."""

    listing_id: UUID
    company_id: UUID
    message: str
    contact_email: str
    status: InquiryStatus = InquiryStatus.OPEN
    contact_phone: str | None = None

    def validate(self) -> None:
        if not self.message:
            raise ValidationDomainError("Inquiry message is required")
        if not self.contact_email:
            raise ValidationDomainError("Inquiry contact_email is required")
