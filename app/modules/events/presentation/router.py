from fastapi import APIRouter, Depends, HTTPException

from app.modules.events.infrastructure.models import ActivityEventModel
from app.modules.events.presentation.schemas import EventIn, EventOut
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import (
    current_user_id,
    is_platform_admin,
    membership_company_ids,
)
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


@router.get(
    "/reports",
)
async def list_reports(
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
    event_type: str = "user_reported",
):
    if not is_platform_admin(current_user):
        raise HTTPException(status_code=403, detail="Forbidden")
    from sqlalchemy import desc, select

    from app.modules.events.infrastructure.models import ActivityEventModel

    q = await session.execute(
        select(ActivityEventModel)
        .where(ActivityEventModel.event_type == event_type)
        .order_by(desc(ActivityEventModel.created_at))
        .limit(100)
    )
    rows = q.scalars().all()
    return {
        "items": [
            {
                "id": str(r.id),
                "eventType": r.event_type,
                "actorUserId": r.actor_user_id,
                "companyId": r.company_id,
                "listingId": r.listing_id,
                "payload": r.payload,
                "createdAt": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }
