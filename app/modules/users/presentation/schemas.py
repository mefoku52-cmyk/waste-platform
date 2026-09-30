from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.modules.users.domain.enums import UserStatus
from app.shared.application.email_domain_validator import (
    validate_email_domain,
)


class UserCreateRequest(BaseModel):
    email: EmailStr
    firstName: str
    lastName: str
    password: str = Field(min_length=8)
    displayName: str | None = None
    phone: str | None = None
    locale: str | None = None
    timezone: str | None = None

    @field_validator("email")
    @classmethod
    def _reject_fake_domains(cls, v: str) -> str:
        return validate_email_domain(str(v))


class UserUpdateRequest(BaseModel):
    firstName: str | None = None
    lastName: str | None = None
    displayName: str | None = None
    phone: str | None = None
    locale: str | None = None
    timezone: str | None = None


class UserStatusTransitionRequest(BaseModel):
    toStatus: UserStatus


class UserData(BaseModel):
    id: UUID
    status: UserStatus
    email: EmailStr
    firstName: str
    lastName: str
    displayName: str | None
    phone: str | None
    locale: str | None
    timezone: str | None
    lastLoginAt: datetime | None
    createdAt: datetime
    createdByUserId: UUID | None
    updatedAt: datetime
    updatedByUserId: UUID | None


class UserResponse(BaseModel):
    data: UserData


class PaginationMeta(BaseModel):
    page: int
    pageSize: int
    total: int


class PaginatedUsersResponse(BaseModel):
    items: list[UserData]
    meta: PaginationMeta
