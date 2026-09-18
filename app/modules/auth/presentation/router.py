from fastapi import APIRouter, Depends, Request, Response, status

from app.modules.auth.presentation.dependencies import (
    get_auth_service,
    get_login_service,
    get_logout_service,
    get_password_reset_service,
    get_refresh_token_service,
)
from app.modules.auth.presentation.schemas import (
    AuthTokenPairResponse,
    CurrentUserResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MembershipContext,
    RefreshTokenRequest,
    ResetPasswordRequest,
)
from app.modules.users.presentation.mappers import to_user_data
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.error_schemas import error_responses

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=AuthTokenPairResponse,
    responses=error_responses(401, 422, 500),
)
async def login(request: Request, payload: LoginRequest, service=Depends(get_login_service)):
    from app.shared.infrastructure.rate_limit import check_rate_limit, client_ip

    ip = client_ip(request)
    check_rate_limit(f"login:{ip}", limit=10, period=60)
    check_rate_limit(f"login:email:{payload.email.lower().strip()}", limit=5, period=60)
    dto = await service.execute(email=payload.email, password=payload.password)
    return AuthTokenPairResponse(
        accessToken=dto.access_token,
        refreshToken=dto.refresh_token,
        tokenType=dto.token_type,
        expiresIn=dto.expires_in,
    )


@router.post(
    "/refresh",
    response_model=AuthTokenPairResponse,
    responses=error_responses(401, 422, 500),
)
async def refresh_token(payload: RefreshTokenRequest, service=Depends(get_refresh_token_service)):
    dto = await service.execute(refresh_token=payload.refreshToken)
    return AuthTokenPairResponse(
        accessToken=dto.access_token,
        refreshToken=dto.refresh_token,
        tokenType=dto.token_type,
        expiresIn=dto.expires_in,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(401, 422, 500),
)
async def logout(payload: LogoutRequest, service=Depends(get_logout_service)):
    await service.execute(refresh_token=payload.refreshToken)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    responses=error_responses(401, 403, 500),
)
async def me(current_user=Depends(require_current_user), service=Depends(get_auth_service)):
    from app.shared.presentation.authorization import is_platform_admin

    context = current_user
    return CurrentUserResponse(
        user=to_user_data(context.user),
        roleCodes=context.role_codes,
        isPlatformAdmin=is_platform_admin(context),
        memberships=[
            MembershipContext(
                id=item["id"],
                companyId=item["companyId"],
                membershipRole=item["membershipRole"],
                status=item["status"],
                isPrimaryContact=item["isPrimaryContact"],
            )
            for item in context.memberships
        ],
    )


@router.post(
    "/forgot-password",
    responses=error_responses(400, 422, 500),
)
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    svc=Depends(get_password_reset_service),
):
    from app.shared.infrastructure.rate_limit import check_rate_limit, client_ip

    ip = client_ip(request)
    check_rate_limit(f"forgot:{ip}", limit=5, period=60)
    check_rate_limit(f"forgot:email:{payload.email.lower().strip()}", limit=3, period=300)
    return await svc.request_reset(payload.email)


@router.post(
    "/reset-password",
    responses=error_responses(400, 404, 422, 500),
)
async def reset_password(
    payload: ResetPasswordRequest,
    svc=Depends(get_password_reset_service),
):
    await svc.reset_password(payload.token, payload.newPassword)
    return {"ok": True, "message": "Heslo bolo zmenené."}
