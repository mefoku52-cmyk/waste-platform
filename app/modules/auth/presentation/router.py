from fastapi import APIRouter, Depends, Request, Response, status

from app.modules.auth.presentation.dependencies import (
    get_auth_service,
    get_email_verification_service,
    get_jwt_service,
    get_login_service,
    get_logout_service,
    get_password_reset_service,
    get_refresh_token_service,
    get_two_factor_service,
)
from app.modules.auth.presentation.schemas import (
    AuthTokenPairResponse,
    CurrentUserResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MembershipContext,
    RefreshTokenRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TwoFactorDisableRequest,
    TwoFactorLoginRequest,
    TwoFactorSetupResponse,
    TwoFactorStatusResponse,
    TwoFactorVerifyRequest,
    TwoFactorVerifyResponse,
    VerifyEmailRequest,
)
from app.modules.users.presentation.mappers import to_user_data
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.error_schemas import error_responses

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    responses=error_responses(401, 422, 500),
)
async def login(request: Request, payload: LoginRequest, service=Depends(get_login_service)):
    from app.shared.infrastructure.rate_limit import check_rate_limit, client_ip

    ip = client_ip(request)
    await check_rate_limit(f"login:{ip}", limit=10, period=60)
    await check_rate_limit(f"login:email:{payload.email.lower().strip()}", limit=5, period=60)
    result = await service.execute(email=payload.email, password=payload.password)

    if result.requires_2fa:
        return LoginResponse(
            requires2fa=True,
            twoFactorToken=result.two_factor_token,
        )

    return LoginResponse(
        requires2fa=False,
        accessToken=result.access_token,
        refreshToken=result.refresh_token,
        tokenType=result.token_type,
        expiresIn=result.expires_in,
    )


@router.post(
    "/2fa/login",
    response_model=LoginResponse,
    responses=error_responses(401, 422, 500),
)
async def two_factor_login(
    request: Request,
    payload: TwoFactorLoginRequest,
    service=Depends(get_login_service),
    jwt_service=Depends(get_jwt_service),
):
    from app.shared.infrastructure.rate_limit import check_rate_limit, client_ip

    ip = client_ip(request)
    await check_rate_limit(f"2fa-login:{ip}", limit=10, period=60)

    try:
        decoded = await jwt_service.decode_2fa_token(payload.twoFactorToken)
    except Exception as exc:
        from app.shared.domain.exceptions import UnauthorizedDomainError

        raise UnauthorizedDomainError("Invalid or expired 2FA token") from exc

    user_id = decoded.get("sub")
    if not user_id:
        from app.shared.domain.exceptions import UnauthorizedDomainError

        raise UnauthorizedDomainError("Invalid 2FA token payload")

    result = await service.complete_login(user_id=str(user_id), code=payload.code)
    return LoginResponse(
        requires2fa=False,
        accessToken=result.access_token,
        refreshToken=result.refresh_token,
        tokenType=result.token_type,
        expiresIn=result.expires_in,
    )


# ─────────────────────────────────────────────────────────────
# 2FA SETTINGS (vyzaduje prihlasenie)
# ─────────────────────────────────────────────────────────────


@router.get(
    "/2fa/status",
    response_model=TwoFactorStatusResponse,
    responses=error_responses(401, 500),
)
async def two_factor_status(
    current_user=Depends(require_current_user),
    service=Depends(get_two_factor_service),
):
    from app.shared.presentation.authorization import current_user_id

    uid = current_user_id(current_user)
    if not uid:
        from app.shared.domain.exceptions import UnauthorizedDomainError

        raise UnauthorizedDomainError("Authentication required")
    st = await service.status(user_id=uid)
    return TwoFactorStatusResponse(
        enabled=st.enabled,
        verifiedAt=st.verified_at,
    )


@router.post(
    "/2fa/setup",
    response_model=TwoFactorSetupResponse,
    responses=error_responses(401, 500),
)
async def two_factor_setup(
    current_user=Depends(require_current_user),
    service=Depends(get_two_factor_service),
):
    from app.shared.presentation.authorization import current_user_email, current_user_id

    uid = current_user_id(current_user)
    email = current_user_email(current_user)
    if not uid:
        from app.shared.domain.exceptions import UnauthorizedDomainError

        raise UnauthorizedDomainError("Authentication required")
    res = await service.setup(user_id=uid, email=email or "user")
    return TwoFactorSetupResponse(
        secret=res.secret,
        otpauthUri=res.otpauth_uri,
        qrSvg=res.qr_svg,
    )


@router.post(
    "/2fa/verify",
    response_model=TwoFactorVerifyResponse,
    responses=error_responses(400, 401, 500),
)
async def two_factor_verify(
    payload: TwoFactorVerifyRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_two_factor_service),
):
    from app.shared.domain.exceptions import ValidationDomainError
    from app.shared.presentation.authorization import current_user_id

    uid = current_user_id(current_user)
    if not uid:
        from app.shared.domain.exceptions import UnauthorizedDomainError

        raise UnauthorizedDomainError("Authentication required")
    ok, codes = await service.verify_and_enable(user_id=uid, code=payload.code)
    if not ok:
        raise ValidationDomainError("Nesprávny alebo expirovaný kód.")
    return TwoFactorVerifyResponse(ok=True, backupCodes=codes)


@router.post(
    "/2fa/disable",
    response_model=TwoFactorVerifyResponse,
    responses=error_responses(400, 401, 500),
)
async def two_factor_disable(
    payload: TwoFactorDisableRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_two_factor_service),
):
    from app.shared.domain.exceptions import ValidationDomainError
    from app.shared.presentation.authorization import current_user_id

    uid = current_user_id(current_user)
    if not uid:
        from app.shared.domain.exceptions import UnauthorizedDomainError

        raise UnauthorizedDomainError("Authentication required")
    ok = await service.disable(user_id=uid, code=payload.code)
    if not ok:
        raise ValidationDomainError("Nesprávny kód.")
    return TwoFactorVerifyResponse(ok=True, backupCodes=[])


@router.post(
    "/2fa/backup-codes/regenerate",
    response_model=TwoFactorVerifyResponse,
    responses=error_responses(400, 401, 500),
)
async def two_factor_regenerate_backup_codes(
    payload: TwoFactorDisableRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_two_factor_service),
):
    from app.shared.domain.exceptions import ValidationDomainError
    from app.shared.presentation.authorization import current_user_id

    uid = current_user_id(current_user)
    if not uid:
        from app.shared.domain.exceptions import UnauthorizedDomainError

        raise UnauthorizedDomainError("Authentication required")
    codes = await service.regenerate_backup_codes(user_id=uid, code=payload.code)
    if codes is None:
        raise ValidationDomainError("Nesprávny kód alebo 2FA nie je aktívna.")
    return TwoFactorVerifyResponse(ok=True, backupCodes=codes)


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
    await check_rate_limit(f"forgot:{ip}", limit=5, period=60)
    await check_rate_limit(f"forgot:email:{payload.email.lower().strip()}", limit=3, period=300)
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


@router.post(
    "/verify-email",
    responses=error_responses(400, 422, 500),
)
async def verify_email(
    payload: VerifyEmailRequest,
    svc=Depends(get_email_verification_service),
):
    return await svc.verify(payload.token)


@router.post(
    "/resend-verification",
    responses=error_responses(400, 422, 429, 500),
)
async def resend_verification(
    request: Request,
    payload: ResendVerificationRequest,
    svc=Depends(get_email_verification_service),
):
    from app.shared.infrastructure.rate_limit import check_rate_limit, client_ip

    ip = client_ip(request)
    await check_rate_limit(f"resend-verify:{ip}", limit=5, period=60)
    await check_rate_limit(
        f"resend-verify:email:{payload.email.lower().strip()}", limit=3, period=300
    )
    return await svc.request_verification(payload.email)
