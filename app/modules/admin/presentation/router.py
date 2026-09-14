from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import (
    require_admin,
    require_current_user,
)

"""admin API router."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status

from app.shared.domain.exceptions import ValidationDomainError

from ..application.services import AdminAuditEntryService
from ..domain.entities import AdminAuditEntryEntity
from .dependencies import get_admin_service
from .schemas import (
    AdminAuditEntryCreateRequest,
    AdminAuditEntryData,
    AdminAuditEntryResponse,
    PaginatedAdminAuditEntriesResponse,
    PaginationMeta,
)

router = APIRouter(prefix="/admin", tags=["admin-audit"])


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


@router.get(
    "",
    response_model=PaginatedAdminAuditEntriesResponse,
    summary="List current user's audit entries",
    operation_id="listCurrentUserAuditEntries",
)
async def list_admin(
    page: int = 1,
    limit: int = 20,
    current_user=Depends(require_current_user),
    service: AdminAuditEntryService = Depends(get_admin_service),
):
    uid = getattr(getattr(current_user, "user", None), "id", None) or getattr(
        current_user, "id", None
    )
    items = await service.list_by_actor(uid, page, limit)
    total = await service.count_by_actor(uid)
    return PaginatedAdminAuditEntriesResponse(
        items=[_to_data(e) for e in items],
        meta=PaginationMeta(page=page, pageSize=limit, total=total),
    )


@router.get(
    "/all",
    response_model=PaginatedAdminAuditEntriesResponse,
    summary="List all audit entries",
    operation_id="listAllAuditEntries",
)
async def list_all_admin(
    page: int = 1,
    limit: int = 20,
    current_user=Depends(require_admin),
    service: AdminAuditEntryService = Depends(get_admin_service),
):
    items = await service.list_all(page, limit)
    total = await service.count_all()
    return PaginatedAdminAuditEntriesResponse(
        items=[_to_data(e) for e in items],
        meta=PaginationMeta(page=page, pageSize=limit, total=total),
    )


@router.get(
    "/stats",
    summary="Platform stats for admin dashboard",
)
async def admin_stats(
    current_user=Depends(require_admin),
    session=Depends(get_db_session),
):
    from sqlalchemy import text

    users = (await session.execute(text("SELECT COUNT(*) FROM users"))).scalar_one()
    listings = (await session.execute(text("SELECT COUNT(*) FROM listings"))).scalar_one()
    companies = (await session.execute(text("SELECT COUNT(*) FROM companies"))).scalar_one()
    pending = (
        await session.execute(
            text("SELECT COUNT(*) FROM companies WHERE status = 'verification_submitted'")
        )
    ).scalar_one()
    return {
        "total_users": int(users),
        "total_listings": int(listings),
        "total_companies": int(companies),
        "pending_verifications": int(pending),
    }


@router.get(
    "/users",
    summary="List users for admin dashboard",
)
async def admin_list_users(
    current_user=Depends(require_admin),
    session=Depends(get_db_session),
):
    from sqlalchemy import text

    rows = await session.execute(
        text(
            "SELECT id, email, first_name, last_name, status, last_login_at, created_at "
            "FROM users ORDER BY created_at DESC LIMIT 200"
        )
    )
    items = []
    for r in rows.mappings():
        items.append(
            {
                "id": str(r["id"]),
                "email": r["email"],
                "firstName": r["first_name"],
                "lastName": r["last_name"],
                "status": r["status"],
                "lastLogin": r["last_login_at"].isoformat() if r["last_login_at"] else None,
                "createdAt": r["created_at"].isoformat() if r["created_at"] else None,
                "roleCodes": ["admin"] if r["email"] == "admin@cmep.dev" else [],
            }
        )
    return {
        "items": items,
        "data": items,
        "meta": {"total": len(items)},
    }


@router.get(
    "/{id}",
    response_model=AdminAuditEntryResponse,
    summary="Get audit entry by ID",
    operation_id="getAuditEntryById",
)
async def get_admin(id: str, service: AdminAuditEntryService = Depends(get_admin_service)):
    entity = await service.get_by_id(id)
    if entity is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="AdminAuditEntry not found",
        )
    return AdminAuditEntryResponse(data=_to_data(entity))


@router.post(
    "",
    response_model=AdminAuditEntryResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create audit entry",
    operation_id="createAuditEntry",
)
async def create_admin(
    request: AdminAuditEntryCreateRequest,
    service: AdminAuditEntryService = Depends(get_admin_service),
):
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
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message
        ) from exc
    return AdminAuditEntryResponse(data=_to_data(created))
