from app.shared.infrastructure.db.session import get_db_session
from fastapi import APIRouter, Depends, Request, Response, status

from app.modules.auth.presentation.dependencies import (
    get_auth_service,
    get_login_service,
    get_logout_service,
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

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthTokenPairResponse)
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


@router.post("/forgot-password")
async def forgot_password(request: Request, payload: ForgotPasswordRequest, session=Depends(get_db_session)):
    from app.shared.infrastructure.rate_limit import check_rate_limit, client_ip
    ip = client_ip(request)
    check_rate_limit(f"forgot:{ip}", limit=5, period=60)
    check_rate_limit(f"forgot:email:{payload.email.lower().strip()}", limit=3, period=300)
    from app.modules.users.infrastructure.repositories import SqlAlchemyUserRepository
    from app.shared.application.passwords import PasswordService
    from app.modules.auth.application.password_reset import PasswordResetService

    repo = SqlAlchemyUserRepository(session)
    svc = PasswordResetService(user_repo=repo, password_service=PasswordService())
    return await svc.request_reset(payload.email)


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, session=Depends(get_db_session)):
    from app.modules.users.infrastructure.repositories import SqlAlchemyUserRepository
    from app.shared.application.passwords import PasswordService
    from app.modules.auth.application.password_reset import PasswordResetService
    from app.shared.domain.exceptions import ValidationDomainError, NotFoundDomainError
    from fastapi import HTTPException

    repo = SqlAlchemyUserRepository(session)
    svc = PasswordResetService(user_repo=repo, password_service=PasswordService())
    try:
        await svc.reset_password(payload.token, payload.newPassword)
    except ValidationDomainError as exc:
        raise HTTPException(status_code=400, detail=getattr(exc, "message", str(exc)))
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=404, detail=getattr(exc, "message", str(exc)))
    return {"ok": True, "message": "Heslo bolo zmenené."}

