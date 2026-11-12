"""inspections API router.

Poznámky k bezpečnosti:
  - Všetky účastnícke endpointy sú viazané na JWT (require_current_user);
    companyId sa vždy odvodí z memberships, NIKDY z tela requestu.
  - Interné endpointy (verify, events) sú pre streamovaciu službu a vyžadujú
    hlavičku X-CMEP-Internal-Key; bez konfigurácie sú fail-closed (403).
"""

from fastapi import APIRouter, Depends, Header, Query
from uuid import UUID

from app.modules.auth.presentation.schemas import CurrentUserResponse
from app.shared.presentation import authorization as authz
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.error_schemas import error_responses

from .dependencies import get_inspection_service
from .schemas import (
    ActiveInspectionResponse,
    ConsentResponse,
    CreateInspectionRequest,
    CreateInspectionResponse,
    InspectionDataOut,
    InspectionEventIn,
    InspectionEventOut,
    InspectionResponse,
    InspectionVerifyResponse,
    JoinInspectionRequest,
    JoinInspectionResponse,
    inspection_data_out,
)

router = APIRouter(prefix="/inspections", tags=["inspections"])


def _user_id(current_user) -> str:
    u = getattr(current_user, "user", None)
    uid = getattr(u, "id", None) if u is not None else getattr(current_user, "id", None)
    if uid is None:
        raise authz.ForbiddenDomainError("User id not available")
    return str(uid)


def _company_ids(current_user) -> list[str]:
    return authz.membership_company_ids(current_user)


@router.post(
    "",
    response_model=CreateInspectionResponse,
    status_code=201,
    responses=error_responses(401, 403, 404, 409, 422, 500),
)
async def create_inspection(
    payload: CreateInspectionRequest,
    current_user: CurrentUserResponse = Depends(require_current_user),
    service=Depends(get_inspection_service),
):
    """Vlastník ponuky spúšťa živú obhliadku → publisher prístup (URL s tokenom)."""
    result = await service.create_inspection(
        user_id=_user_id(current_user),
        company_ids=_company_ids(current_user),
        listing_id=str(payload.listingId),
    )
    return CreateInspectionResponse(
        inspection=inspection_data_out(result["inspection"]),
        role="publisher",
        publishUrl=result["publishUrl"],
        expiresIn=result["expiresIn"],
    )


@router.get(
    "",
    response_model=ActiveInspectionResponse,
    responses=error_responses(401, 403, 404, 500),
)
async def active_inspection(
    listingId: UUID = Query(...),
    current_user=Depends(require_current_user),
    service=Depends(get_inspection_service),
):
    """Aktuálna obhliadka ponuky + čo smie klient urobiť (UI gating)."""
    return await service.active_inspection_for_listing(
        user_id=_user_id(current_user),
        company_ids=_company_ids(current_user),
        listing_id=str(listingId),
    )


@router.post(
    "/join",
    response_model=JoinInspectionResponse,
    responses=error_responses(401, 403, 404, 409, 422, 500),
)
async def join_inspection(
    payload: JoinInspectionRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_inspection_service),
):
    """Druhá strana (viewer) sa pripája — vráti viewer URL vrátane Room ID."""
    result = await service.join_inspection(
        user_id=_user_id(current_user),
        company_ids=_company_ids(current_user),
        inspection_id=str(payload.inspectionId) if payload.inspectionId else None,
        listing_id=str(payload.listingId) if payload.listingId else None,
        thread_id=str(payload.threadId) if payload.threadId else None,
        wait_room_seconds=payload.waitRoomSeconds,
    )
    return JoinInspectionResponse(
        inspection=inspection_data_out(result["inspection"]),
        role="viewer",
        viewerUrl=result["viewerUrl"],
        expiresIn=result["expiresIn"],
        roomId=result["roomId"],
    )


@router.get(
    "/{inspection_id}",
    response_model=InspectionResponse,
    responses=error_responses(401, 403, 404, 500),
)
async def get_inspection(
    inspection_id: str,
    current_user=Depends(require_current_user),
    service=Depends(get_inspection_service),
):
    """Stav obhliadky — len pre účastníkov (owner firma alebo priradený viewer)."""
    result = await service.get_inspection(
        user_id=_user_id(current_user),
        company_ids=_company_ids(current_user),
        inspection_id=inspection_id,
    )
    return InspectionResponse(data=inspection_data_out(result["inspection"]))


@router.post(
    "/{inspection_id}/publisher-link",
    responses=error_responses(401, 403, 404, 409, 500),
)
async def publisher_link(
    inspection_id: str,
    current_user=Depends(require_current_user),
    service=Depends(get_inspection_service),
):
    """Znovu vystaví publisher URL (nový token, rovnaká obhliadka)."""
    return await service.publisher_link(
        user_id=_user_id(current_user),
        company_ids=_company_ids(current_user),
        inspection_id=inspection_id,
    )


@router.post(
    "/{inspection_id}/recording-consent",
    response_model=ConsentResponse,
    responses=error_responses(401, 403, 404, 409, 500),
)
async def grant_recording_consent(
    inspection_id: str,
    current_user=Depends(require_current_user),
    service=Depends(get_inspection_service),
):
    """Výslovný súhlas vlastníka ponuky s nahrávaním (bez neho rec=0 v tokenoch)."""
    result = await service.set_recording_consent(
        user_id=_user_id(current_user),
        company_ids=_company_ids(current_user),
        inspection_id=inspection_id,
    )
    return ConsentResponse(data=inspection_data_out(result["inspection"]))


@router.post(
    "/{inspection_id}/end",
    response_model=InspectionResponse,
    responses=error_responses(401, 403, 404, 409, 500),
)
async def end_inspection(
    inspection_id: str,
    current_user=Depends(require_current_user),
    service=Depends(get_inspection_service),
):
    """Korektné ukončenie obhliadky vlastníkom (platformová strana)."""
    result = await service.end_inspection(
        user_id=_user_id(current_user),
        company_ids=_company_ids(current_user),
        inspection_id=inspection_id,
    )
    return InspectionResponse(data=inspection_data_out(result["inspection"]))


# ─── Interné rozhranie pre CMEP Streaming (X-CMEP-Internal-Key) ───────────


@router.get(
    "/{inspection_id}/verify",
    response_model=InspectionVerifyResponse,
    responses=error_responses(403, 404, 500),
)
async def verify_inspection(
    inspection_id: str,
    x_cmep_internal_key: str | None = Header(default=None),
    sub: str | None = Query(default=None),
    role: str | None = Query(default=None),
    service=Depends(get_inspection_service),
):
    """Verify pre HttpAdapter streamingu — fail-closed (403/404/ok=False)."""
    return await service.verify_for_streaming(
        internal_key=x_cmep_internal_key,
        inspection_id=inspection_id,
        sub=sub,
        role=role,
    )


@router.post(
    "/events",
    response_model=InspectionEventOut,
    responses=error_responses(403, 404, 422, 500),
)
async def record_inspection_event(
    payload: InspectionEventIn,
    x_cmep_internal_key: str | None = Header(default=None),
    service=Depends(get_inspection_service),
):
    """Ingest eventov zo streamingu — idempotentný podľa eventUid."""
    return await service.record_event(
        internal_key=x_cmep_internal_key,
        event_uid=payload.eventUid,
        inspection_id=str(payload.inspectionId),
        event_type=payload.eventType,
        actor_sub=payload.actorSub,
        room_id=payload.roomId,
        role=payload.role,
        reason=payload.reason,
    )
