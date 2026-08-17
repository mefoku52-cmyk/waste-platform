"""analytics API router."""

from fastapi import APIRouter, Depends, HTTPException, status as http_status

from app.shared.domain.exceptions import NotFoundDomainError, ValidationDomainError

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


@router.get(""), response_model=PaginatedAnalyticsEventsResponse)
async def list_analytics(page: int = 1, limit: int = 20, service: AnalyticsEventService = Depends(get_analytics_service)):
    items = await service.list_all(page, limit)
    total = await service.count_all()
    return PaginatedAnalyticsEventsResponse(items=[_to_data(e) for e in items], meta=PaginationMeta(page=page, pageSize=limit, total=total))


@router.get("/{id}", response_model=AnalyticsEventResponse)
async def get_analytic(id: str, service: AnalyticsEventService = Depends(get_analytics_service)):
    entity = await service.get_by_id(id)
    if entity is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="AnalyticsEvent not found")
    return AnalyticsEventResponse(data=_to_data(entity))


@router.post(""), response_model=AnalyticsEventResponse, status_code=http_status.HTTP_201_CREATED)
async def create_analytic(request: AnalyticsEventCreateRequest, service: AnalyticsEventService = Depends(get_analytics_service)):
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
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc
    return AnalyticsEventResponse(data=_to_data(created))


@router.put("/{id}", response_model=AnalyticsEventResponse)
async def update_analytic(id: str, request: AnalyticsEventUpdateRequest, service: AnalyticsEventService = Depends(get_analytics_service)):
    existing = await service.get_by_id(id)
    if existing is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="AnalyticsEvent not found")
    updated_entity = AnalyticsEventEntity(
        event_type=request.eventType if request.eventType is not None else existing.event_type,
        entity_type=request.entityType if request.entityType is not None else existing.entity_type,
        entity_id=request.entityId if request.entityId is not None else existing.entity_id,
        company_id=request.companyId if request.companyId is not None else existing.company_id,
        event_metadata=request.eventMetadata if request.eventMetadata is not None else existing.event_metadata,
        recorded_at=request.recordedAt if request.recordedAt is not None else existing.recorded_at,
    )
    try:
        result = await service.update(id, updated_entity)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except ValidationDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc
    return AnalyticsEventResponse(data=_to_data(result))


@router.delete("/{id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_analytic(id: str, service: AnalyticsEventService = Depends(get_analytics_service)):
    try:
        await service.delete(id)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
