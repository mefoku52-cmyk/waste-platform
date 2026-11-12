"""inspections application DTOs."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.inspections.domain.enums import InspectionState


@dataclass(slots=True)
class StreamingToken:
    """Kratke HMAC opravnenie pre CMEP Streaming (format zhodny s auth.js)."""

    token: str
    expires_in: int
    inspection_id: UUID
    role: str
    company_id: UUID | None


@dataclass(slots=True)
class InspectionData:
    id: UUID
    listing_id: UUID
    room_id: str | None
    owner_user_id: UUID
    owner_company_id: UUID
    viewer_user_id: UUID | None
    viewer_company_id: UUID | None
    viewer_thread_id: UUID | None
    state: InspectionState
    consent_to_record: bool
    created_at: datetime
    updated_at: datetime
    ended_at: datetime | None = None
