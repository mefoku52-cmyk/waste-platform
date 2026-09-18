"""analytics API router."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status

from app.shared.domain.exceptions import (
    ForbiddenDomainError,
    NotFoundDomainError,
    ValidationDomainError,
)
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import (
    is_platform_admin,
    membership_company_ids,
    require_company_admin,
)
from app.shared.presentation.error_schemas import error_responses

from ..application.services import AnalyticsEventService
from ..domain.entities import AnalyticsEventEntity
from .dependencies import get_analytics_service
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
