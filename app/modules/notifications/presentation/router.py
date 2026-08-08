"""notifications API router."""

from fastapi import APIRouter, Depends, HTTPException, status as http_status

from app.shared.domain.exceptions import NotFoundDomainError, ValidationDomainError

from ..application.services import NotificationService
from ..domain.entities import NotificationEntity
from .dependencies import get_notifications_service
from .schemas import (
    NotificationCreateRequest,
    NotificationData,
    NotificationResponse,
    NotificationUpdateRequest,
    PaginatedNotificationsResponse,
    PaginationMeta,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _to_data(entity: NotificationEntity) -> NotificationData:
    return NotificationData(
        id=entity.id,
        userId=entity.user_id,
        type=entity.type,
        title=entity.title,
        message=entity.message,
        isRead=entity.is_read,
        relatedEntityId=entity.related_entity_id,
        createdAt=entity.created_at,
        updatedAt=entity.updated_at,
    )


@router.get("/", response_model=PaginatedNotificationsResponse)
async def list_notifications(page: int = 1, limit: int = 20, service: NotificationService = Depends(get_notifications_service)):
    items = await service.list_all(page, limit)
    total = await service.count_all()
    return PaginatedNotificationsResponse(items=[_to_data(e) for e in items], meta=PaginationMeta(page=page, pageSize=limit, total=total))


@router.get("/{id}", response_model=NotificationResponse)
async def get_notification(id: str, service: NotificationService = Depends(get_notifications_service)):
    entity = await service.get_by_id(id)
    if entity is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return NotificationResponse(data=_to_data(entity))


@router.post("/", response_model=NotificationResponse, status_code=http_status.HTTP_201_CREATED)
async def create_notification(request: NotificationCreateRequest, service: NotificationService = Depends(get_notifications_service)):
    entity = NotificationEntity(
        user_id=request.userId,
        type=request.type,
        title=request.title,
        message=request.message,
        is_read=request.isRead,
        related_entity_id=request.relatedEntityId,
    )
    try:
        created = await service.create(entity)
    except ValidationDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc
    return NotificationResponse(data=_to_data(created))


@router.put("/{id}", response_model=NotificationResponse)
async def update_notification(id: str, request: NotificationUpdateRequest, service: NotificationService = Depends(get_notifications_service)):
    existing = await service.get_by_id(id)
    if existing is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Notification not found")
    updated_entity = NotificationEntity(
        user_id=request.userId if request.userId is not None else existing.user_id,
        type=request.type if request.type is not None else existing.type,
        title=request.title if request.title is not None else existing.title,
        message=request.message if request.message is not None else existing.message,
        is_read=request.isRead if request.isRead is not None else existing.is_read,
        related_entity_id=request.relatedEntityId if request.relatedEntityId is not None else existing.related_entity_id,
    )
    try:
        result = await service.update(id, updated_entity)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except ValidationDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc
    return NotificationResponse(data=_to_data(result))


@router.delete("/{id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_notification(id: str, service: NotificationService = Depends(get_notifications_service)):
    try:
        await service.delete(id)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
