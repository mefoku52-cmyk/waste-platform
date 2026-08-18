from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.modules.company_memberships.domain.enums import (
    CompanyMembershipRole,
    CompanyMembershipStatus,
)


class CompanyMembershipCreateRequest(BaseModel):
    userId: UUID
    membershipRole: CompanyMembershipRole
    isPrimaryContact: bool = False


class CompanyMembershipUpdateRequest(BaseModel):
    membershipRole: CompanyMembershipRole | None = None
    isPrimaryContact: bool | None = None


class CompanyMembershipStatusTransitionRequest(BaseModel):
    toStatus: CompanyMembershipStatus


class CompanyMembershipData(BaseModel):
    id: UUID
    status: CompanyMembershipStatus
    companyId: UUID
    userId: UUID
    membershipRole: CompanyMembershipRole
    isPrimaryContact: bool
    invitedAt: datetime | None
    joinedAt: datetime | None
    leftAt: datetime | None
    createdAt: datetime
    createdByUserId: UUID | None
    updatedAt: datetime
    updatedByUserId: UUID | None


class CompanyMembershipResponse(BaseModel):
    data: CompanyMembershipData


class PaginationMeta(BaseModel):
    page: int
    pageSize: int
    total: int


class PaginatedCompanyMembershipsResponse(BaseModel):
    items: list[CompanyMembershipData]
    meta: PaginationMeta
