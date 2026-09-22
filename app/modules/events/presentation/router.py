from fastapi import APIRouter, Depends, HTTPException

from app.modules.events.infrastructure.models import ActivityEventModel
from app.modules.events.presentation.schemas import EventIn, EventOut
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import current_user_id, membership_company_ids
from app.shared.presentation.error_schemas import error_responses

ALLOWED = {
    "listing_viewed",
    "recommendation_shown",
    "inquiry_opened",
    "route_calculated",
}

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventOut, responses=error_responses(401, 422, 500))
async def create_event(
    body: EventIn,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
):
    kind = body.eventType.strip()
    if kind not in ALLOWED:
        raise HTTPException(status_code=422, detail="Unknown eventType")
    company_id = body.companyId
    if not company_id:
        memberships = list(membership_company_ids(current_user) or [])
        company_id = str(memberships[0]) if memberships else None
    row = ActivityEventModel(
        event_type=kind,
        actor_user_id=str(current_user_id(current_user)),
        company_id=company_id,
        listing_id=body.listingId,
        payload=body.payload,
    )
    session.add(row)
    commit = getattr(session, "commit", None)
    if commit:
        result = commit()
        if hasattr(result, "__await__"):
            await result
    flush = getattr(session, "flush", None)
    if flush:
        result = flush()
        if hasattr(result, "__await__"):
            await result
    return EventOut(id=str(row.id), eventType=row.event_type)
