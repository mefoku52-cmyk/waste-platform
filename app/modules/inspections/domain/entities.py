"""inspections domain entities."""

from dataclasses import dataclass
from uuid import UUID

from app.modules.inspections.domain.enums import InspectionState
from app.shared.domain.base import AuditFields
from app.shared.domain.exceptions import ValidationDomainError


@dataclass(slots=True)
class InspectionEntity(AuditFields):
    """Ziva obhliadka viazana na ponuku (listing) a dve strany.

    Identifikatory:
      listing_id          — ponuka (Offer), z ktorej obhliadka vznikla
      room_id             — Room ID pridelene streamovacou sluzbou (nullable)
      owner_user_id / owner_company_id     — publisher (vlastnik ponuky)
      viewer_user_id / viewer_company_id  — viewer (druha strana), po prvom join-e
    """

    listing_id: UUID
    owner_user_id: UUID
    owner_company_id: UUID
    room_id: str | None = None
    viewer_user_id: UUID | None = None
    viewer_company_id: UUID | None = None
    viewer_thread_id: UUID | None = None
    state: InspectionState = InspectionState.CREATED
    consent_to_record: bool = False
    recording_consent_at: object | None = None
    ended_at: object | None = None

    def validate(self) -> None:
        if not self.listing_id:
            raise ValidationDomainError("Inspection listing_id is required")
        if not self.owner_user_id:
            raise ValidationDomainError("Inspection owner_user_id is required")
        if not self.owner_company_id:
            raise ValidationDomainError("Inspection owner_company_id is required")
