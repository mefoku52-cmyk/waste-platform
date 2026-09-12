"""notifications API router."""

from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status

from app.shared.domain.exceptions import ForbiddenDomainError, NotFoundDomainError
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.error_schemas import error_responses

from ..application.services import NotificationService
from ..domain.entities import NotificationEntity
from .dependencies import get_notifications_service
from .schemas import (
    NotificationCreateRequest,
    NotificationData,
    NotificationResponse,
    PaginatedNotificationsResponse,
    PaginationMeta,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _current_user_id(current_user):
    return getattr(getattr(current_user, "user", None), "id", None) or getattr(
        current_user, "id", None
    )


def _ensure_notification_owner(entity: NotificationEntity, current_user) -> None:
    if str(entity.user_id) != str(_current_user_id(current_user)):
        raise ForbiddenDomainError("You do not have access to this notification")


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


@router.get(
    "",
    response_model=PaginatedNotificationsResponse,
    responses=error_responses(401, 403, 422, 500),
)
async def list_notifications(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    limit: int | None = Query(default=None, ge=1, le=100, include_in_schema=False),
    current_user=Depends(require_current_user),
    service: NotificationService = Depends(get_notifications_service),
):
    uid = _current_user_id(current_user)
    effective_page_size = limit or pageSize
    items = await service.list_by_user_id(uid, page, effective_page_size)
    total = await service.count_by_user_id(uid)
    return PaginatedNotificationsResponse(
        items=[_to_data(e) for e in items],
        meta=PaginationMeta(page=page, pageSize=effective_page_size, total=total),
    )


@router.get(
    "/{id}",
    response_model=NotificationResponse,
    responses=error_responses(401, 403, 404, 500),
)
async def get_notification(
    id: str,
    current_user=Depends(require_current_user),
    service: NotificationService = Depends(get_notifications_service),
):
    entity = await service.get_by_id(id)
    if entity is None:
        raise NotFoundDomainError(f"Notification {id} not found")
    _ensure_notification_owner(entity, current_user)
    return NotificationResponse(data=_to_data(entity))


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=http_status.HTTP_201_CREATED,
    responses=error_responses(401, 403, 409, 422, 500),
)
async def create_notification(
    request: NotificationCreateRequest,
    current_user=Depends(require_current_user),
    service: NotificationService = Depends(get_notifications_service),
):
    current_uid = _current_user_id(current_user)
    if str(request.userId) != str(current_uid):
        raise ForbiddenDomainError("You cannot create notifications for another user")

    entity = NotificationEntity(
        user_id=request.userId,
        type=request.type,
        title=request.title,
        message=request.message,
        is_read=request.isRead,
        related_entity_id=request.relatedEntityId,
    )
    created = await service.create(entity)
    return NotificationResponse(data=_to_data(created))


@router.post(
    "/{id}/mark-read",
    response_model=NotificationResponse,
    responses=error_responses(401, 403, 404, 409, 422, 500),
)
async def mark_notification_read(
    id: str,
    current_user=Depends(require_current_user),
    service: NotificationService = Depends(get_notifications_service),
):
    entity = await service.get_by_id(id)
    if entity is None:
        raise NotFoundDomainError(f"Notification {id} not found")
    _ensure_notification_owner(entity, current_user)

    result = await service.mark_read(id)
    return NotificationResponse(data=_to_data(result))


@router.post(
    "/{id}/mark-unread",
    response_model=NotificationResponse,
    responses=error_responses(401, 403, 404, 409, 422, 500),
)
async def mark_notification_unread(
    id: str,
    current_user=Depends(require_current_user),
    service: NotificationService = Depends(get_notifications_service),
):
    entity = await service.get_by_id(id)
    if entity is None:
        raise NotFoundDomainError(f"Notification {id} not found")
    _ensure_notification_owner(entity, current_user)

    result = await service.mark_unread(id)
    return NotificationResponse(data=_to_data(result))


@router.delete(
    "/{id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    responses=error_responses(401, 403, 404, 500),
)
async def delete_notification(
    id: str,
    current_user=Depends(require_current_user),
    service: NotificationService = Depends(get_notifications_service),
):
    entity = await service.get_by_id(id)
    if entity is None:
        raise NotFoundDomainError(f"Notification {id} not found")
    _ensure_notification_owner(entity, current_user)
    await service.delete(id)
