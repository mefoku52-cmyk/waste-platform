from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.modules.users.presentation.schemas import UserData


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refreshToken: str


class LogoutRequest(BaseModel):
    refreshToken: str | None = None


class AuthTokenPairResponse(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str
    expiresIn: int


class MembershipContext(BaseModel):
    id: UUID
    companyId: UUID
    membershipRole: str
    status: str
    isPrimaryContact: bool


class CurrentUserResponse(BaseModel):
    user: UserData
    roleCodes: list[str]
    memberships: list[MembershipContext]
    # Server-authoritativny signal platform-admin opravnenia. Frontend ho pouziva
    # namiesto lokalneho odvodzovania z roleCodes (tenant rola `admin` NIE je
    # platform admin).
    isPlatformAdmin: bool = False


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    newPassword: str


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=10, max_length=512)


class ResendVerificationRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)


# ─────────────────────────────────────────────────────────────
# 2FA (TOTP)
# ─────────────────────────────────────────────────────────────


class TwoFactorLoginRequest(BaseModel):
    twoFactorToken: str = Field(min_length=10, max_length=512)
    code: str = Field(min_length=6, max_length=16)


class TwoFactorSetupResponse(BaseModel):
    secret: str
    otpauthUri: str
    qrSvg: str


class TwoFactorVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=16)


class TwoFactorVerifyResponse(BaseModel):
    ok: bool
    backupCodes: list[str] = []


class TwoFactorStatusResponse(BaseModel):
    enabled: bool
    verifiedAt: datetime | None = None


class TwoFactorDisableRequest(BaseModel):
    code: str = Field(min_length=6, max_length=16)


class LoginResponse(BaseModel):
    """Rozsireny login response — bud tokeny alebo 2FA challenge."""

    requires2fa: bool = False
    twoFactorToken: str | None = None

    accessToken: str | None = None
    refreshToken: str | None = None
    tokenType: str = "Bearer"
    expiresIn: int = 0
