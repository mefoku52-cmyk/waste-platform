import json

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

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
    "user_feedback",
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


# ============================================================
# Public contact endpoint (bez auth) — pre landing page formulár
# ============================================================


class ContactIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=320)
    company: str | None = Field(default=None, max_length=200)
    message: str = Field(min_length=1, max_length=4000)


@router.post("/contact", response_model=EventOut)
async def submit_contact(
    body: ContactIn,
    request: Request,
    session=Depends(get_db_session),
):
    """Uloží kontaktný formulár z landing page.

    Bez auth. Rate-limit cez IP hash (max 5 requestov / hodinu / IP).
    """
    # Jednoduchý rate limit cez X-Forwarded-For
    import hashlib
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import func, select

    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
        request.client.host if request.client else "unknown"
    )
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]

    one_hour_ago = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)
    cnt_stmt = select(func.count(ActivityEventModel.id)).where(
        ActivityEventModel.event_type == "contact_submitted",
        ActivityEventModel.payload.contains(ip_hash),
        ActivityEventModel.created_at >= one_hour_ago,
    )
    cnt_result = await session.execute(cnt_stmt)
    count = int(cnt_result.scalar() or 0)
    if count >= 5:
        raise HTTPException(status_code=429, detail="Too many submissions. Skús neskôr.")

    payload_data = {
        "name": body.name.strip(),
        "email": body.email.strip(),
        "company": (body.company or "").strip(),
        "message": body.message.strip(),
        "ip_hash": ip_hash,
        "user_agent": (request.headers.get("user-agent") or "")[:300],
    }

    row = ActivityEventModel(
        event_type="contact_submitted",
        actor_user_id=None,
        company_id=None,
        listing_id=None,
        payload=json.dumps(payload_data, ensure_ascii=False)[:2000],
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

    from app.shared.application.side_effects import notify_platform_admins

    email_lines = [
        "Nový kontakt z webu trc-cmep.sk",
        "",
        f"Meno: {payload_data['name']}",
        f"E-mail: {payload_data['email']}",
    ]
    if payload_data["company"]:
        email_lines.append(f"Firma: {payload_data['company']}")
    email_lines.extend(["", "Správa:", payload_data["message"]])
    await notify_platform_admins(
        subject=f"Kontakt z webu: {payload_data['name']}",
        body="\n".join(email_lines),
        reply_to=payload_data["email"],
    )

    return EventOut(id=str(row.id), eventType="contact_submitted")
