"""Admin-only security events endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_platform.infrastructure.models import SecurityEventModel
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_admin

router = APIRouter(
    prefix="/agent-platform/security",
    tags=["agent-platform-security"],
)


@router.get("/events")
async def list_security_events(
    limit: int = Query(default=50, ge=1, le=200),
    kind: str | None = Query(default=None),
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    stmt = select(SecurityEventModel).order_by(desc(SecurityEventModel.occurred_at))
    if kind:
        stmt = stmt.where(SecurityEventModel.kind == kind)
    stmt = stmt.limit(limit)
    rows = (await session.execute(stmt)).scalars().all()
    return {
        "items": [
            {
                "eventId": r.event_id,
                "kind": r.kind,
                "pattern": r.pattern,
                "source": r.source,
                "actorId": r.actor_id,
                "target": r.target,
                "confidence": r.confidence,
                "sourceObservationId": r.source_observation_id,
                "occurredAt": r.occurred_at.isoformat() if r.occurred_at else None,
            }
            for r in rows
        ],
        "count": len(rows),
    }
