"""analytics API router."""

import json
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.modules.analytics.infrastructure.models import AnalyticsEventModel
from app.shared.domain.exceptions import (
    ForbiddenDomainError,
    NotFoundDomainError,
    ValidationDomainError,
)
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import (
    is_platform_admin,
    membership_company_ids,
    require_company_admin,
)
from app.shared.presentation.error_schemas import error_responses

from ..application.acquisition import (
    AcquisitionEventInput,
    AcquisitionTrackingService,
)
from ..application.services import AnalyticsEventService
from ..domain.entities import AnalyticsEventEntity
from .dependencies import get_analytics_repo, get_analytics_service
from .schemas import (
    AnalyticsEventCreateRequest,
    AnalyticsEventData,
    AnalyticsEventResponse,
    AnalyticsEventUpdateRequest,
    PaginatedAnalyticsEventsResponse,
    PaginationMeta,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _to_data(entity: AnalyticsEventEntity) -> AnalyticsEventData:
    return AnalyticsEventData(
        id=entity.id,
        eventType=entity.event_type,
        entityType=entity.entity_type,
        entityId=entity.entity_id,
        companyId=entity.company_id,
        eventMetadata=entity.event_metadata,
        recordedAt=entity.recorded_at,
        createdAt=entity.created_at,
        updatedAt=entity.updated_at,
    )


def _tenant_company_ids(current_user) -> list[str] | None:
    """None = bez obmedzenia (platform admin). Inak company IDs clenstva."""
    if is_platform_admin(current_user):
        return None
    return membership_company_ids(current_user)


def _require_event_access(entity: AnalyticsEventEntity, current_user) -> None:
    """Platform admin vidi vsetko; tenant len eventy svojej firmy."""
    if is_platform_admin(current_user):
        return
    company_id = entity.company_id
    if company_id is None:
        raise ForbiddenDomainError("You do not have access to this analytics event")
    require_company_admin(current_user, company_id)


@router.get(
    "",
    response_model=PaginatedAnalyticsEventsResponse,
    summary="List analytics events",
    operation_id="listAnalyticsEvents",
    responses=error_responses(401, 403, 422, 500),
)
async def list_analytics(
    page: int = 1,
    limit: int = 20,
    current_user=Depends(require_current_user),
    service: AnalyticsEventService = Depends(get_analytics_service),
):
    company_ids = _tenant_company_ids(current_user)
    items = await service.list_all(page, limit, company_ids=company_ids)
    total = await service.count_all(company_ids=company_ids)
    return PaginatedAnalyticsEventsResponse(
        items=[_to_data(e) for e in items],
        meta=PaginationMeta(page=page, pageSize=limit, total=total),
    )


@router.get(
    "/{id}",
    response_model=AnalyticsEventResponse,
    summary="Get analytics event by ID",
    operation_id="getAnalyticsEventById",
    responses=error_responses(401, 403, 404, 500),
)
async def get_analytic(
    id: str,
    current_user=Depends(require_current_user),
    service: AnalyticsEventService = Depends(get_analytics_service),
):
    entity = await service.get_by_id(id)
    if entity is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="AnalyticsEvent not found",
        )
    _require_event_access(entity, current_user)
    return AnalyticsEventResponse(data=_to_data(entity))


@router.post(
    "",
    response_model=AnalyticsEventResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create analytics event",
    operation_id="createAnalyticsEvent",
    responses=error_responses(401, 403, 409, 422, 500),
)
async def create_analytic(
    request: AnalyticsEventCreateRequest,
    current_user=Depends(require_current_user),
    service: AnalyticsEventService = Depends(get_analytics_service),
):
    if not is_platform_admin(current_user):
        if request.companyId is None:
            raise ForbiddenDomainError("companyId is required for tenant analytics events")
        require_company_admin(current_user, request.companyId, action="write analytics for")

    entity = AnalyticsEventEntity(
        event_type=request.eventType,
        entity_type=request.entityType,
        entity_id=request.entityId,
        company_id=request.companyId,
        event_metadata=request.eventMetadata,
        recorded_at=request.recordedAt,
    )
    try:
        created = await service.create(entity)
    except ValidationDomainError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message
        ) from exc
    return AnalyticsEventResponse(data=_to_data(created))


@router.patch(
    "/{id}",
    response_model=AnalyticsEventResponse,
    summary="Update analytics event",
    operation_id="updateAnalyticsEvent",
    responses=error_responses(401, 403, 404, 422, 500),
)
async def update_analytic(
    id: str,
    request: AnalyticsEventUpdateRequest,
    current_user=Depends(require_current_user),
    service: AnalyticsEventService = Depends(get_analytics_service),
):
    existing = await service.get_by_id(id)
    if existing is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="AnalyticsEvent not found",
        )
    _require_event_access(existing, current_user)

    target_company_id = request.companyId if request.companyId is not None else existing.company_id
    if not is_platform_admin(current_user):
        require_company_admin(current_user, target_company_id, action="write analytics for")

    updated_entity = AnalyticsEventEntity(
        event_type=request.eventType if request.eventType is not None else existing.event_type,
        entity_type=request.entityType if request.entityType is not None else existing.entity_type,
        entity_id=request.entityId if request.entityId is not None else existing.entity_id,
        company_id=target_company_id,
        event_metadata=request.eventMetadata
        if request.eventMetadata is not None
        else existing.event_metadata,
        recorded_at=request.recordedAt if request.recordedAt is not None else existing.recorded_at,
    )
    try:
        result = await service.update(id, updated_entity)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except ValidationDomainError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message
        ) from exc
    return AnalyticsEventResponse(data=_to_data(result))


@router.delete(
    "/{id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    summary="Delete analytics event",
    operation_id="deleteAnalyticsEvent",
    responses=error_responses(401, 403, 404, 500),
)
async def delete_analytic(
    id: str,
    current_user=Depends(require_current_user),
    service: AnalyticsEventService = Depends(get_analytics_service),
):
    existing = await service.get_by_id(id)
    if existing is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="AnalyticsEvent not found",
        )
    _require_event_access(existing, current_user)
    try:
        await service.delete(id)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


# Acquisition tracking endpoint.


class AcquisitionEventRequest(BaseModel):
    event_type: str = Field(min_length=1, max_length=120)
    entity_type: str = Field(default="acquisition", max_length=120)
    entity_id: UUID | None = None
    company_id: UUID | None = None

    utm_source: str | None = Field(default=None, max_length=255)
    utm_medium: str | None = Field(default=None, max_length=255)
    utm_campaign: str | None = Field(default=None, max_length=255)
    utm_content: str | None = Field(default=None, max_length=255)
    utm_term: str | None = Field(default=None, max_length=255)

    anonymous_id: str | None = Field(default=None, max_length=255)
    fbp: str | None = Field(default=None, max_length=255)
    fbc: str | None = Field(default=None, max_length=255)

    landing_page: str | None = Field(default=None, max_length=2000)
    referrer: str | None = Field(default=None, max_length=2000)


@router.post(
    "/acquisition/events",
    status_code=http_status.HTTP_201_CREATED,
    summary="Record acquisition event",
    operation_id="recordAcquisitionEvent",
)
async def record_acquisition_event(
    request: AcquisitionEventRequest,
    repository=Depends(get_analytics_repo),
):
    service = AcquisitionTrackingService(repository)

    event = await service.record(
        AcquisitionEventInput(
            event_type=request.event_type,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            company_id=request.company_id,
            utm_source=request.utm_source,
            utm_medium=request.utm_medium,
            utm_campaign=request.utm_campaign,
            utm_content=request.utm_content,
            utm_term=request.utm_term,
            anonymous_id=request.anonymous_id,
            fbp=request.fbp,
            fbc=request.fbc,
            landing_page=request.landing_page,
            referrer=request.referrer,
        )
    )

    return {
        "id": str(event.id),
        "event_type": event.event_type,
        "entity_type": event.entity_type,
        "recorded_at": event.recorded_at.isoformat(),
    }


# Admin stats endpoint — agregacia page_view eventov.


@router.get(
    "/admin/stats",
    summary="Get admin analytics stats",
    operation_id="getAdminAnalyticsStats",
)
async def get_admin_stats(
    days: int = 30,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
):
    """Vrati agregovane statistiky navstev landing page.

    Iba pre platform adminov.
    """
    if not is_platform_admin(current_user):
        raise ForbiddenDomainError("Platform admin only")

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=days)

    async def count_since(since: datetime | None, until: datetime | None = None) -> int:
        stmt = select(func.count(AnalyticsEventModel.id)).where(
            AnalyticsEventModel.event_type == "page_view"
        )
        if since is not None:
            stmt = stmt.where(AnalyticsEventModel.recorded_at >= since)
        if until is not None:
            stmt = stmt.where(AnalyticsEventModel.recorded_at < until)
        result = await session.execute(stmt)
        return int(result.scalar() or 0)

    total = await count_since(None)
    today = await count_since(today_start)
    yesterday = await count_since(yesterday_start, today_start)
    week = await count_since(week_start)
    month = await count_since(month_start)

    # Unique visitors today — parsuj event_metadata JSON
    rows_today = (
        (
            await session.execute(
                select(AnalyticsEventModel.event_metadata).where(
                    AnalyticsEventModel.event_type == "page_view",
                    AnalyticsEventModel.recorded_at >= today_start,
                )
            )
        )
        .scalars()
        .all()
    )

    anon_ids = set()
    for meta in rows_today:
        if not meta:
            continue
        try:
            data = json.loads(meta)
            aid = data.get("anonymous_id")
            if aid:
                anon_ids.add(aid)
        except Exception:
            pass
    unique_today = len(anon_ids)

    # Daily breakdown pre poslednych N dni
    rows_month = (
        (
            await session.execute(
                select(AnalyticsEventModel.recorded_at).where(
                    AnalyticsEventModel.event_type == "page_view",
                    AnalyticsEventModel.recorded_at >= month_start,
                )
            )
        )
        .scalars()
        .all()
    )

    daily: dict[str, int] = {}
    for dt in rows_month:
        key = dt.date().isoformat()
        daily[key] = daily.get(key, 0) + 1

    # Top sources z poslednych N dni
    rows_meta = (
        (
            await session.execute(
                select(AnalyticsEventModel.event_metadata).where(
                    AnalyticsEventModel.event_type == "page_view",
                    AnalyticsEventModel.recorded_at >= month_start,
                )
            )
        )
        .scalars()
        .all()
    )

    sources: dict[str, int] = {}
    for meta in rows_meta:
        if not meta:
            continue
        try:
            data = json.loads(meta)
            ref = (data.get("referrer") or "").strip() or "direct"
            utm = (data.get("utm_source") or "").strip()
            key = f"{ref}" + (f" · {utm}" if utm else "")
            sources[key] = sources.get(key, 0) + 1
        except Exception:
            pass
    top_sources = sorted(sources.items(), key=lambda x: -x[1])[:10]

    return {
        "total": total,
        "today": today,
        "yesterday": yesterday,
        "week": week,
        "month": month,
        "uniqueToday": unique_today,
        "daily": daily,
        "topSources": [{"source": s, "count": c} for s, c in top_sources],
    }
