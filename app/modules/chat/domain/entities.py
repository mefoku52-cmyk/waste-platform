"""chat domain entities."""

from dataclasses import dataclass
from uuid import UUID

from app.modules.chat.domain.enums import ChatThreadStatus
from app.shared.domain.base import AuditFields
from app.shared.domain.exceptions import ValidationDomainError


@dataclass(slots=True)
class ChatThreadEntity(AuditFields):
    """Chat thread - konverzacia medzi dvoma stranami."""

    initiator_user_id: UUID
    initiator_company_id: UUID | None
    recipient_user_id: UUID
    recipient_company_id: UUID | None
    subject: str
    listing_id: UUID | None = None
    status: ChatThreadStatus = ChatThreadStatus.OPEN
    last_message_at: object | None = None

    def validate(self) -> None:
        if not self.subject:
            raise ValidationDomainError("Chat subject is required")
        if self.initiator_user_id == self.recipient_user_id:
            raise ValidationDomainError("Nemozes chatovat sam so sebou")


@dataclass(slots=True)
class ChatMessageEntity(AuditFields):
    """Chat message."""

    thread_id: UUID
    sender_user_id: UUID
    sender_company_id: UUID | None
    body: str
    read_at: object | None = None

    def validate(self) -> None:
        if not self.body or not self.body.strip():
            raise ValidationDomainError("Sprava nemoze byt prazdna")
        if len(self.body) > 5000:
            raise ValidationDomainError("Sprava je prilis dlha (max 5000 znakov)")
