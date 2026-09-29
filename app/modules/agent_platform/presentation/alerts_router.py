"""Admin-only alerts endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_platform.application.alerts.alert_service import DefaultAlertService
from app.modules.agent_platform.infrastructure.models import AlertRecordModel
from app.modules.agent_platform.infrastructure.persistence.alert_repository import (
    SqlAlchemyAlertRepository,
)
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_admin
from app.shared.presentation.authorization import current_user_id

router = APIRouter(
    prefix="/agent-platform/alerts",
    tags=["agent-platform-alerts"],
)


class ResolveRequest(BaseModel):
    resolution: str


@router.get("")
async def list_alerts(
    limit: int = Query(default=50, ge=1, le=200),
    status: str | None = Query(default=None),
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    stmt = select(AlertRecordModel).order_by(desc(AlertRecordModel.created_at))
    if status:
        stmt = stmt.where(AlertRecordModel.status == status)
    stmt = stmt.limit(limit)
    rows = (await session.execute(stmt)).scalars().all()
    return {
        "items": [
            {
                "alertId": r.alert_id,
                "category": r.category,
                "severity": r.severity,
                "source": r.source,
                "actorId": r.actor_id,
                "event": r.event,
                "status": r.status,
                "createdAt": r.created_at.isoformat() if r.created_at else None,
                "assignedTo": r.assigned_to,
                "resolution": r.resolution,
            }
            for r in rows
        ],
        "count": len(rows),
    }


@router.post("/{alert_id}/ack")
async def acknowledge_alert(
    alert_id: str,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    svc = DefaultAlertService(repository=SqlAlchemyAlertRepository(session))
    actor = current_user_id(current_user) or "admin"
    try:
        alert = await svc.acknowledge(alert_id, actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"alertId": alert.alert_id, "status": alert.status.value}


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    payload: ResolveRequest,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    svc = DefaultAlertService(repository=SqlAlchemyAlertRepository(session))
    actor = current_user_id(current_user) or "admin"
    try:
        alert = await svc.resolve(alert_id, actor, payload.resolution)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "alertId": alert.alert_id,
        "status": alert.status.value,
        "resolution": alert.resolution,
    }
