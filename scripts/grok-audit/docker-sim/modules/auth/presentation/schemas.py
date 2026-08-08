from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

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
