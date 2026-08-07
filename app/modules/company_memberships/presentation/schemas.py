from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CompanyMembershipCreateRequest(BaseModel):
    userId: UUID
    membershipRole: str
    isPrimaryContact: bool = False


class CompanyMembershipUpdateRequest(BaseModel):
    membershipRole: str | None = None
    isPrimaryContact: bool | None = None


class CompanyMembershipStatusTransitionRequest(BaseModel):
    toStatus: str


class CompanyMembershipData(BaseModel):
    id: UUID
    status: str
    companyId: UUID
    userId: UUID
    membershipRole: str
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


class PaginatedCompanyMembershipsResponse(BaseModel):
    items: list[CompanyMembershipData]
    meta: dict
