"""compliance API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ComplianceRecordCreateRequest(BaseModel):
    companyId: UUID
    regulationType: str
    documentRef: str | None = None
    validUntil: datetime | None = None
    notes: str | None = None


class ComplianceRecordUpdateRequest(BaseModel):
    companyId: UUID | None = None
    regulationType: str | None = None
    documentRef: str | None = None
    validUntil: datetime | None = None
    notes: str | None = None
    status: str | None = None


class ComplianceRecordData(BaseModel):
    id: UUID
    companyId: UUID
    regulationType: str
    documentRef: str | None
    validUntil: datetime | None
    notes: str | None
    status: str
    createdAt: datetime
    updatedAt: datetime


class ComplianceRecordResponse(BaseModel):
    data: ComplianceRecordData


class PaginationMeta(BaseModel):
    page: int
    pageSize: int
    total: int


class PaginatedComplianceRecordsResponse(BaseModel):
    items: list[ComplianceRecordData]
    meta: PaginationMeta
