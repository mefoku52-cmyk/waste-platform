from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.modules.users.presentation.dependencies import (
    get_create_user_service,
    get_get_user_service,
    get_list_users_service,
    get_password_service,
    get_transition_user_status_service,
    get_update_user_service,
)
from app.modules.users.presentation.mappers import to_user_data
from app.modules.users.presentation.schemas import (
    PaginatedUsersResponse,
    PaginationMeta,
    UserCreateRequest,
    UserResponse,
    UserStatusTransitionRequest,
    UserUpdateRequest,
)
from app.shared.application.passwords import PasswordService
from app.shared.presentation.auth_dependencies import require_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=PaginatedUsersResponse)
async def list_users(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=25, ge=1, le=100),
    status: str | None = None,
    companyId: UUID | None = None,
    q: str | None = None,
    current_user=Depends(require_current_user),
    service=Depends(get_list_users_service),
):
    items, total = await service.execute(status=status, company_id=companyId, q=q, page=page, page_size=pageSize)
    return PaginatedUsersResponse(
        items=[to_user_data(item) for item in items],
        meta=PaginationMeta(page=page, pageSize=pageSize, total=total),
    )


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    payload: UserCreateRequest,
    service=Depends(get_create_user_service),
    password_service: PasswordService = Depends(get_password_service),
):
    dto = await service.execute(
        email=payload.email,
        password_hash=password_service.hash_password(payload.password),
        first_name=payload.firstName,
        last_name=payload.lastName,
        display_name=payload.displayName,
        phone=payload.phone,
        locale=payload.locale,
        timezone=payload.timezone,
        actor_user_id=None,
    )
    return UserResponse(data=to_user_data(dto))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user=Depends(require_current_user),
    service=Depends(get_get_user_service),
):
    dto = await service.execute(user_id)
    return UserResponse(data=to_user_data(dto))


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    payload: UserUpdateRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_update_user_service),
):
    dto = await service.execute(
        user_id=user_id,
        first_name=payload.firstName,
        last_name=payload.lastName,
        display_name=payload.displayName,
        phone=payload.phone,
        locale=payload.locale,
        timezone=payload.timezone,
        actor_user_id=current_user.user.id,
    )
    return UserResponse(data=to_user_data(dto))


@router.patch("/{user_id}/status", response_model=UserResponse)
async def transition_user_status(
    user_id: UUID,
    payload: UserStatusTransitionRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_transition_user_status_service),
):
    dto = await service.execute(user_id=user_id, to_status=payload.toStatus, actor_user_id=current_user.user.id)
    return UserResponse(data=to_user_data(dto))
