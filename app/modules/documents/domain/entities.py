"""documents domain entities."""

from dataclasses import dataclass
from uuid import UUID

from app.modules.documents.domain.enums import DocumentStatus
from app.shared.domain.base import AuditFields
from app.shared.domain.exceptions import ValidationDomainError


@dataclass(slots=True)
class DocumentEntity(AuditFields):
    """Document entity."""

    title: str
    document_type: str
    file_url: str
    company_id: UUID
    status: DocumentStatus = DocumentStatus.PENDING
    listing_id: UUID | None = None

    def validate(self) -> None:
        if not self.title:
            raise ValidationDomainError("Document title is required")
        if not self.document_type:
            raise ValidationDomainError("Document document_type is required")
        if not self.file_url:
            raise ValidationDomainError("Document file_url is required")
