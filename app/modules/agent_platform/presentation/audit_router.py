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


from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel as _BM

from app.modules.agent_platform.application.audit.audit_service import (
    DefaultAuditService,
)
from app.modules.agent_platform.domain.audit.audit_action import (
    AuditAction,
)
from app.modules.agent_platform.domain.audit.audit_record import (
    AuditRecord,
)
from app.modules.agent_platform.domain.audit.audit_subject import (
    AuditSubject,
)
from app.modules.agent_platform.infrastructure.audit.audit_store import (
    SqlAlchemyAuditStore,
)
from app.shared.presentation.authorization import current_user_id


class _AuditIn(_BM):
    action: str
    actor_type: str = "admin"
    subject_type: str | None = None
    subject_id: str | None = None
    reason: str | None = None
    metadata: dict = {}


@router.post("/record")
async def record_audit(
    payload: _AuditIn,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Manualny zapis auditu. Pouzivatel: admin. Append-only."""
    from fastapi import HTTPException

    try:
        action = AuditAction(payload.action)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Neznama akcia: {payload.action}") from exc

    subject = None
    if payload.subject_type and payload.subject_id:
        subject = AuditSubject(
            subject_type=payload.subject_type,
            subject_id=payload.subject_id,
        )

    record = AuditRecord(
        audit_id=str(uuid4()),
        actor_id=current_user_id(current_user),
        actor_type=payload.actor_type,
        action=action,
        subject=subject,
        occurred_at=datetime.now(UTC),
        success=True,
        reason=payload.reason,
        metadata=payload.metadata,
    )
    store = SqlAlchemyAuditStore(session)
    svc = DefaultAuditService(store=store)
    saved = await svc.record(record)
    return {"auditId": saved.audit_id, "action": action.value}
