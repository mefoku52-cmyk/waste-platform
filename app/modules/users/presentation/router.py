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
from app.shared.presentation.authorization import current_user_id, is_platform_admin
from app.shared.presentation.error_schemas import error_responses

router = APIRouter(prefix="/users", tags=["users"])


def _require_self_or_admin(current_user, user_id) -> None:
    """Platform admin smie vsetko; bezny user len svoj vlastny zaznam."""
    from app.shared.domain.exceptions import ForbiddenDomainError

    if is_platform_admin(current_user):
        return
    if str(current_user_id(current_user)) != str(user_id):
        raise ForbiddenDomainError("You do not have access to this user")


@router.get(
    "",
    response_model=PaginatedUsersResponse,
    responses=error_responses(401, 403, 422, 500),
)
async def list_users(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=25, ge=1, le=100),
    status: str | None = None,
    companyId: UUID | None = None,
    q: str | None = None,
    current_user=Depends(require_current_user),
    service=Depends(get_list_users_service),
):
    # Zoznam vsetkych userov je platform-admin operacia (PII).
    from app.shared.domain.exceptions import ForbiddenDomainError

    if not is_platform_admin(current_user):
        raise ForbiddenDomainError("Platform admin access required")

    items, total = await service.execute(
        status=status, company_id=companyId, q=q, page=page, page_size=pageSize
    )
    return PaginatedUsersResponse(
        items=[to_user_data(item) for item in items],
        meta=PaginationMeta(page=page, pageSize=pageSize, total=total),
    )


@router.post(
    "",
    response_model=UserResponse,
    status_code=201,
    responses=error_responses(409, 422, 500),
)
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


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    responses=error_responses(401, 403, 404, 500),
)
async def get_user(
    user_id: UUID,
    current_user=Depends(require_current_user),
    service=Depends(get_get_user_service),
):
    _require_self_or_admin(current_user, user_id)
    dto = await service.execute(user_id)
    return UserResponse(data=to_user_data(dto))


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    responses=error_responses(401, 403, 404, 409, 422, 500),
)
async def update_user(
    user_id: UUID,
    payload: UserUpdateRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_update_user_service),
):
    _require_self_or_admin(current_user, user_id)
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


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
    responses=error_responses(401, 403, 404, 409, 422, 500),
)
async def transition_user_status(
    user_id: UUID,
    payload: UserStatusTransitionRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_transition_user_status_service),
):
    # Zmena stavu (aktivacia/suspendacia) je platform-admin operacia.
    from app.shared.domain.exceptions import ForbiddenDomainError

    if not is_platform_admin(current_user):
        raise ForbiddenDomainError("Platform admin access required")

    dto = await service.execute(
        user_id=user_id, to_status=payload.toStatus, actor_user_id=current_user.user.id
    )
    return UserResponse(data=to_user_data(dto))
