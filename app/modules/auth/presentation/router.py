from fastapi import APIRouter, Depends, Response, status

from app.modules.auth.presentation.dependencies import (
    get_auth_service,
    get_login_service,
    get_logout_service,
    get_refresh_token_service,
)
from app.modules.auth.presentation.schemas import (
    AuthTokenPairResponse,
    CurrentUserResponse,
    LoginRequest,
    LogoutRequest,
    MembershipContext,
    RefreshTokenRequest,
)
from app.modules.users.presentation.mappers import to_user_data
from app.shared.presentation.auth_dependencies import require_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthTokenPairResponse)
async def login(payload: LoginRequest, service=Depends(get_login_service)):
    dto = await service.execute(email=payload.email, password=payload.password)
    return AuthTokenPairResponse(
        accessToken=dto.access_token,
        refreshToken=dto.refresh_token,
        tokenType=dto.token_type,
        expiresIn=dto.expires_in,
    )


@router.post("/refresh", response_model=AuthTokenPairResponse)
async def refresh_token(payload: RefreshTokenRequest, service=Depends(get_refresh_token_service)):
    dto = await service.execute(refresh_token=payload.refreshToken)
    return AuthTokenPairResponse(
        accessToken=dto.access_token,
        refreshToken=dto.refresh_token,
        tokenType=dto.token_type,
        expiresIn=dto.expires_in,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: LogoutRequest, service=Depends(get_logout_service)):
    await service.execute(refresh_token=payload.refreshToken)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=CurrentUserResponse)
async def me(current_user=Depends(require_current_user), service=Depends(get_auth_service)):
    context = current_user
    return CurrentUserResponse(
        user=to_user_data(context.user),
        roleCodes=context.role_codes,
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
