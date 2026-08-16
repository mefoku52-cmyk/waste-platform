from app.shared.presentation.auth_dependencies import require_admin
from app.shared.presentation.auth_dependencies import require_current_user
"""admin API router."""

from fastapi import APIRouter, Depends, HTTPException, status as http_status

from app.shared.domain.exceptions import NotFoundDomainError, ValidationDomainError

from ..application.services import AdminAuditEntryService
from ..domain.entities import AdminAuditEntryEntity
from ..domain.enums import AdminAuditEntryStatus
from .dependencies import get_admin_service
from .schemas import (
    AdminAuditEntryCreateRequest,
    AdminAuditEntryData,
    AdminAuditEntryResponse,
    AdminAuditEntryUpdateRequest,
    PaginatedAdminAuditEntrysResponse,
    PaginationMeta,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _to_data(entity: AdminAuditEntryEntity) -> AdminAuditEntryData:
    return AdminAuditEntryData(
        id=entity.id,
        actorUserId=entity.actor_user_id,
        action=entity.action,
        targetType=entity.target_type,
        targetId=entity.target_id,
        details=entity.details,
        status=entity.status.value,
        createdAt=entity.created_at,
        updatedAt=entity.updated_at,
    )


@router.get("/", response_model=PaginatedAdminAuditEntrysResponse)
async def list_admin(
    page: int = 1,
    limit: int = 20,
    current_user=Depends(require_current_user),
    service: AdminAuditEntryService = Depends(get_admin_service),
):
    uid = getattr(getattr(current_user, "user", None), "id", None) or getattr(current_user, "id", None)
    items = await service.list_by_actor(uid, page, limit)
    total = await service.count_by_actor(uid)
    return PaginatedAdminAuditEntrysResponse(items=[_to_data(e) for e in items], meta=PaginationMeta(page=page, pageSize=limit, total=total))




@router.get("/all", response_model=PaginatedAdminAuditEntrysResponse)
async def list_all_admin(
    page: int = 1,
    limit: int = 20,
    current_user=Depends(require_admin),
    service: AdminAuditEntryService = Depends(get_admin_service),
):
    items = await service.list_all(page, limit)
    total = await service.count_all()
    return PaginatedAdminAuditEntrysResponse(
        items=[_to_data(e) for e in items],
        meta=PaginationMeta(page=page, pageSize=limit, total=total),
    )

@router.get("/{id}", response_model=AdminAuditEntryResponse)
async def get_admin(id: str, service: AdminAuditEntryService = Depends(get_admin_service)):
    entity = await service.get_by_id(id)
    if entity is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="AdminAuditEntry not found")
    return AdminAuditEntryResponse(data=_to_data(entity))


@router.post("/", response_model=AdminAuditEntryResponse, status_code=http_status.HTTP_201_CREATED)
async def create_admin(request: AdminAuditEntryCreateRequest, service: AdminAuditEntryService = Depends(get_admin_service)):
    entity = AdminAuditEntryEntity(
        actor_user_id=request.actorUserId,
        action=request.action,
        target_type=request.targetType,
        target_id=request.targetId,
        details=request.details,
    )
    try:
        created = await service.create(entity)
    except ValidationDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc
    return AdminAuditEntryResponse(data=_to_data(created))


@router.put("/{id}", response_model=AdminAuditEntryResponse)
async def update_admin(id: str, request: AdminAuditEntryUpdateRequest, service: AdminAuditEntryService = Depends(get_admin_service)):
    existing = await service.get_by_id(id)
    if existing is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="AdminAuditEntry not found")
    updated_entity = AdminAuditEntryEntity(
        actor_user_id=request.actorUserId if request.actorUserId is not None else existing.actor_user_id,
        action=request.action if request.action is not None else existing.action,
        target_type=request.targetType if request.targetType is not None else existing.target_type,
        target_id=request.targetId if request.targetId is not None else existing.target_id,
        details=request.details if request.details is not None else existing.details,
        status=AdminAuditEntryStatus(request.status) if request.status is not None else existing.status,
    )
    try:
        result = await service.update(id, updated_entity)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except ValidationDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc
    return AdminAuditEntryResponse(data=_to_data(result))


@router.delete("/{id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_admin(id: str, service: AdminAuditEntryService = Depends(get_admin_service)):
    try:
        await service.delete(id)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
