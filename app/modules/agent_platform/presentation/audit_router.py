"""Admin-only agent audit endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_platform.infrastructure.models import AgentAuditRecordModel
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_admin

router = APIRouter(
    prefix="/agent-platform/audit",
    tags=["agent-platform-audit"],
)


@router.get("/recent")
async def recent_audit(
    limit: int = Query(default=100, ge=1, le=500),
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    stmt = (
        select(AgentAuditRecordModel).order_by(desc(AgentAuditRecordModel.occurred_at)).limit(limit)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return {
        "items": [
            {
                "auditId": r.audit_id,
                "actorId": r.actor_id,
                "actorType": r.actor_type,
                "action": r.action,
                "subjectType": r.subject_type,
                "subjectId": r.subject_id,
                "occurredAt": r.occurred_at.isoformat() if r.occurred_at else None,
                "success": bool(r.success),
                "reason": r.reason,
            }
            for r in rows
        ],
        "count": len(rows),
    }


@router.get("/by-actor/{actor_id}")
async def audit_by_actor(
    actor_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    stmt = (
        select(AgentAuditRecordModel)
        .where(AgentAuditRecordModel.actor_id == actor_id)
        .order_by(desc(AgentAuditRecordModel.occurred_at))
        .limit(limit)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return {
        "actorId": actor_id,
        "items": [
            {
                "auditId": r.audit_id,
                "action": r.action,
                "occurredAt": r.occurred_at.isoformat() if r.occurred_at else None,
                "success": bool(r.success),
                "reason": r.reason,
            }
            for r in rows
        ],
        "count": len(rows),
    }
