"""inspections schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.inspections.application.dto import InspectionData


class CreateInspectionRequest(BaseModel):
    listingId: UUID


class JoinInspectionRequest(BaseModel):
    listingId: UUID | None = None
    inspectionId: UUID | None = None
    threadId: UUID | None = None
    waitRoomSeconds: float = Field(default=6.0, ge=0, le=15)


class InspectionDataOut(BaseModel):
    id: UUID
    listingId: UUID
    roomId: str | None = None
    ownerUserId: UUID
    ownerCompanyId: UUID
    viewerUserId: UUID | None = None
    viewerCompanyId: UUID | None = None
    viewerThreadId: UUID | None = None
    state: str
    consentToRecord: bool
    createdAt: datetime
    updatedAt: datetime
    endedAt: datetime | None = None


class InspectionResponse(BaseModel):
    data: InspectionDataOut


def inspection_data_out(e: InspectionData) -> InspectionDataOut:
    """Prekládacie rozhranie medzi internou (snake) entitou a API DTO (camel)."""
    return InspectionDataOut(
        id=e.id,
        listingId=e.listing_id,
        roomId=e.room_id,
        ownerUserId=e.owner_user_id,
        ownerCompanyId=e.owner_company_id,
        viewerUserId=e.viewer_user_id,
        viewerCompanyId=e.viewer_company_id,
        viewerThreadId=e.viewer_thread_id,
        state=str(e.state.value) if hasattr(e.state, "value") else str(e.state),
        consentToRecord=e.consent_to_record,
        createdAt=e.created_at,
        updatedAt=e.updated_at,
        endedAt=e.ended_at,
    )


class CreateInspectionResponse(BaseModel):
    inspection: InspectionDataOut
    role: str
    publishUrl: str
    expiresIn: int


class JoinInspectionResponse(BaseModel):
    inspection: InspectionDataOut
    role: str
    viewerUrl: str
    expiresIn: int
    roomId: str | None = None


class ActiveInspectionResponse(BaseModel):
    inspection: InspectionDataOut | None = None
    canPublish: bool
    canJoin: bool
    isViewer: bool = False


class ConsentResponse(BaseModel):
    data: InspectionDataOut


class InspectionVerifyResponse(BaseModel):
    ok: bool
    state: str
    reason: str | None = None
    inspectionId: str | None = None
    listingId: str | None = None
    ownerCompanyId: str | None = None
    viewerCompanyId: str | None = None
    consentToRecord: bool | None = None
    roomId: str | None = None


class InspectionEventIn(BaseModel):
    """Ingest zo streamingu — HttpAdapter kontrakt (fail-closed)."""

    eventUid: str = Field(min_length=8, max_length=64)
    inspectionId: UUID
    eventType: str = Field(min_length=3, max_length=64)
    actorSub: str | None = None
    roomId: str | None = None
    role: str | None = Field(default=None, pattern="^(owner|viewer|publisher)$")
    reason: str | None = Field(default=None, max_length=255)


class InspectionEventOut(BaseModel):
    recorded: bool
    duplicate: bool = False
    state: str | None = None
