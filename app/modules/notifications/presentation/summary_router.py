"""Admin pipeline summary.

Exposes a compact JSON with current pipeline counters so the admin UI
or Telegram can show a snapshot without scraping /metrics text format.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import is_platform_admin

router = APIRouter(
    prefix="/admin/metrics",
    tags=["admin-metrics"],
)


class PipelineSummary(BaseModel):
    generated_at: str
    candidates_by_status: dict[str, int]
    sent_last_24h: int
    sent_last_7d: int
    discovery_last_24h: int
    top_bounces_last_7d: int


@router.get("/summary", response_model=PipelineSummary)
async def pipeline_summary(
    current_user=Depends(require_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PipelineSummary:
    """Snapshot of current pipeline state. Admin only."""
    if not is_platform_admin(current_user):
        raise HTTPException(status_code=403, detail="Platform admin access required")

    by_status = await session.execute(
        text("SELECT status, COUNT(*) FROM outreach_candidates GROUP BY status ORDER BY status")
    )
    candidates_by_status = {row[0]: int(row[1]) for row in by_status}

    sent_24h = await session.execute(
        text("SELECT COUNT(*) FROM outreach_candidates WHERE sent_at >= :since"),
        {"since": datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=24)},
    )
    sent_7d = await session.execute(
        text("SELECT COUNT(*) FROM outreach_candidates WHERE sent_at >= :since"),
        {"since": datetime.now(UTC).replace(tzinfo=None) - timedelta(days=7)},
    )

    discovery_24h = await session.execute(
        text("SELECT COUNT(*) FROM outreach_candidates WHERE created_at >= :since"),
        {"since": datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=24)},
    )

    return PipelineSummary(
        generated_at=datetime.now(UTC).isoformat(),
        candidates_by_status=candidates_by_status,
        sent_last_24h=int(sent_24h.scalar() or 0),
        sent_last_7d=int(sent_7d.scalar() or 0),
        discovery_last_24h=int(discovery_24h.scalar() or 0),
        top_bounces_last_7d=0,
    )


__all__ = ["router"]
