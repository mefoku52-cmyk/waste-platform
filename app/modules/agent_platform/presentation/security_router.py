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


from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel as _BM

from app.modules.agent_platform.application.security.security_risk_engine import (
    DefaultSecurityRiskEngine,
)
from app.modules.agent_platform.application.security.security_signal_service import (
    DefaultSecuritySignalService,
)
from app.modules.agent_platform.domain.security.security_observation import (
    SecurityObservation,
)
from app.modules.agent_platform.domain.security.security_pattern import (
    SecurityPattern,
)
from app.modules.agent_platform.infrastructure.security.security_event_store import (
    SqlAlchemySecurityEventStore,
)


class _ObservationIn(_BM):
    pattern: str
    source: str = "manual"
    actor_id: str | None = None
    target: str | None = None
    evidence: dict = {}


@router.post("/evaluate")
async def evaluate_observation(
    payload: _ObservationIn,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Zoberie observation a vrati SecurityDecision (bez zapisu)."""
    from fastapi import HTTPException

    try:
        pattern = SecurityPattern(payload.pattern)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Neznamy pattern: {payload.pattern}") from exc

    from app.modules.agent_platform.application.security.security_engine import (
        DefaultSecurityEngine,
    )

    obs = SecurityObservation(
        observation_id=str(uuid4()),
        pattern=pattern,
        source=payload.source,
        actor_id=payload.actor_id,
        target=payload.target,
        evidence=payload.evidence,
        observed_at=datetime.now(UTC),
    )
    engine = DefaultSecurityEngine()
    decision = await engine.evaluate(obs)
    return {
        "observationId": obs.observation_id,
        "pattern": pattern.value,
        "decision": decision.value if hasattr(decision, "value") else str(decision),
    }


@router.post("/observe")
async def observe_and_signal(
    payload: _ObservationIn,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Vytvori observation -> signal -> risk. Signal sa zapise do DB."""
    from fastapi import HTTPException

    try:
        pattern = SecurityPattern(payload.pattern)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Neznamy pattern: {payload.pattern}") from exc

    obs = SecurityObservation(
        observation_id=str(uuid4()),
        pattern=pattern,
        source=payload.source,
        actor_id=payload.actor_id,
        target=payload.target,
        evidence=payload.evidence,
        observed_at=datetime.now(UTC),
    )
    store = SqlAlchemySecurityEventStore(session)
    signal_svc = DefaultSecuritySignalService(store=store)
    risk_engine = DefaultSecurityRiskEngine()

    signal = await signal_svc.observe(obs)
    risk = await risk_engine.evaluate(signal)

    return {
        "observationId": obs.observation_id,
        "signalId": signal.signal_id,
        "pattern": pattern.value,
        "confidence": float(signal.confidence),
        "riskLevel": risk.level.value if hasattr(risk.level, "value") else str(risk.level),
        "riskScore": float(risk.score),
    }


@router.get("/diagnostics")
async def security_diagnostics(
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Diagnostika: ci tabulky existuju a kolko zaznamov maju."""
    from sqlalchemy import text

    out: dict = {}

    # 1. Existuju tabulky?
    for table in (
        "agent_security_events",
        "agent_alert_records",
        "agent_approval_requests",
        "agent_audit_records",
        "agent_control_state",
    ):
        try:
            r = await session.execute(
                text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = :t"),
                {"t": table},
            )
            exists = int(r.scalar() or 0) > 0
            count = None
            if exists:
                c = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = int(c.scalar() or 0)
            out[table] = {"exists": exists, "count": count}
        except Exception as exc:
            out[table] = {"exists": False, "error": type(exc).__name__}

    # 2. Poslednych 5 udalosti zo security events
    recent = []
    try:
        r = await session.execute(
            text(
                "SELECT event_id, kind, pattern, actor_id, occurred_at "
                "FROM agent_security_events ORDER BY occurred_at DESC LIMIT 5"
            )
        )
        for row in r:
            recent.append(
                {
                    "eventId": str(row[0]),
                    "kind": row[1],
                    "pattern": row[2],
                    "actorId": row[3],
                    "occurredAt": row[4].isoformat() if row[4] else None,
                }
            )
    except Exception as exc:
        recent = [{"error": type(exc).__name__}]

    return {
        "tables": out,
        "recentSecurityEvents": recent,
    }
