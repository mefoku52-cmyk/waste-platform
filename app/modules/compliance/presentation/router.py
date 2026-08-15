from app.shared.presentation.auth_dependencies import require_current_user
"""compliance API router."""

from fastapi import APIRouter, Depends, HTTPException, status as http_status

from app.shared.domain.exceptions import NotFoundDomainError, ValidationDomainError

from ..application.services import ComplianceRecordService
from ..domain.entities import ComplianceRecordEntity
from ..domain.enums import ComplianceRecordStatus
from .dependencies import get_compliance_service
from .schemas import (
    ComplianceRecordCreateRequest,
    ComplianceRecordData,
    ComplianceRecordResponse,
    ComplianceRecordUpdateRequest,
    PaginatedComplianceRecordsResponse,
    PaginationMeta,
)

router = APIRouter(prefix="/compliance", tags=["compliance"])


def _to_data(entity: ComplianceRecordEntity) -> ComplianceRecordData:
    return ComplianceRecordData(
        id=entity.id,
        companyId=entity.company_id,
        regulationType=entity.regulation_type,
        documentRef=entity.document_ref,
        validUntil=entity.valid_until,
        notes=entity.notes,
        status=entity.status.value,
        createdAt=entity.created_at,
        updatedAt=entity.updated_at,
    )


@router.get("/", response_model=PaginatedComplianceRecordsResponse)
async def list_compliance(
    page: int = 1,
    limit: int = 20,
    current_user=Depends(require_current_user),
    service: ComplianceRecordService = Depends(get_compliance_service),
):
    company_ids = []
    for m in (current_user.memberships or []):
        cid = m.get("companyId") if isinstance(m, dict) else getattr(m, "companyId", None)
        if cid is not None:
            company_ids.append(cid)
    items = await service.list_by_company_ids(company_ids, page, limit)
    total = await service.count_by_company_ids(company_ids)
    return PaginatedComplianceRecordsResponse(items=[_to_data(e) for e in items], meta=PaginationMeta(page=page, pageSize=limit, total=total))


@router.get("/{id}", response_model=ComplianceRecordResponse)
async def get_compliance(id: str, service: ComplianceRecordService = Depends(get_compliance_service)):
    entity = await service.get_by_id(id)
    if entity is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="ComplianceRecord not found")
    return ComplianceRecordResponse(data=_to_data(entity))


@router.post("/", response_model=ComplianceRecordResponse, status_code=http_status.HTTP_201_CREATED)
async def create_compliance(request: ComplianceRecordCreateRequest, current_user=Depends(require_current_user), service: ComplianceRecordService = Depends(get_compliance_service)):
    entity = ComplianceRecordEntity(
        company_id=request.companyId,
        regulation_type=request.regulationType,
        document_ref=request.documentRef,
        valid_until=request.validUntil,
        notes=request.notes,
    )
    try:
        created = await service.create(entity)
    except ValidationDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc
    return ComplianceRecordResponse(data=_to_data(created))


@router.put("/{id}", response_model=ComplianceRecordResponse)
async def update_compliance(id: str, request: ComplianceRecordUpdateRequest, service: ComplianceRecordService = Depends(get_compliance_service)):
    existing = await service.get_by_id(id)
    if existing is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="ComplianceRecord not found")
    updated_entity = ComplianceRecordEntity(
        company_id=request.companyId if request.companyId is not None else existing.company_id,
        regulation_type=request.regulationType if request.regulationType is not None else existing.regulation_type,
        document_ref=request.documentRef if request.documentRef is not None else existing.document_ref,
        valid_until=request.validUntil if request.validUntil is not None else existing.valid_until,
        notes=request.notes if request.notes is not None else existing.notes,
        status=ComplianceRecordStatus(request.status) if request.status is not None else existing.status,
    )
    try:
        result = await service.update(id, updated_entity)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except ValidationDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc
    return ComplianceRecordResponse(data=_to_data(result))


@router.delete("/{id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_compliance(id: str, service: ComplianceRecordService = Depends(get_compliance_service)):
    try:
        await service.delete(id)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
