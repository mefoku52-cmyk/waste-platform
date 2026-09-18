from app.shared.presentation.auth_dependencies import require_current_user

"""compliance API router."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status

from app.shared.domain.exceptions import (
    ForbiddenDomainError,
    NotFoundDomainError,
    ValidationDomainError,
)
from app.shared.presentation.authorization import (
    is_platform_admin,
    membership_company_ids,
    require_company_admin,
    require_company_member,
)
from app.shared.presentation.error_schemas import error_responses

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


def _require_access(entity: ComplianceRecordEntity, current_user) -> None:
    """Platform admin vidi vsetko; tenant len záznamy svojej firmy."""
    if is_platform_admin(current_user):
        return
    company_id = entity.company_id
    if company_id is None:
        raise ForbiddenDomainError("You do not have access to this compliance record")
    require_company_member(current_user, company_id, action="access")


@router.get(
    "",
    response_model=PaginatedComplianceRecordsResponse,
    summary="List compliance records",
    operation_id="listComplianceRecords",
    responses=error_responses(401, 403, 422, 500),
)
async def list_compliance(
    page: int = 1,
    limit: int = 20,
    current_user=Depends(require_current_user),
    service: ComplianceRecordService = Depends(get_compliance_service),
):
    if is_platform_admin(current_user):
        # `list_by_company_ids(None)` vracia prazdny zoznam, preto admin
        # pouziva neomezeny variant.
        items = await service.list_all(page, limit)
        total = await service.count_all()
    else:
        company_ids = membership_company_ids(current_user)
        items = await service.list_by_company_ids(company_ids, page, limit)
        total = await service.count_by_company_ids(company_ids)

    return PaginatedComplianceRecordsResponse(
        items=[_to_data(e) for e in items],
        meta=PaginationMeta(page=page, pageSize=limit, total=total),
    )


@router.get(
    "/{id}",
    response_model=ComplianceRecordResponse,
    summary="Get compliance record by ID",
    operation_id="getComplianceRecordById",
    responses=error_responses(401, 403, 404, 500),
)
async def get_compliance(
    id: str,
    current_user=Depends(require_current_user),
    service: ComplianceRecordService = Depends(get_compliance_service),
):
    entity = await service.get_by_id(id)
    if entity is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="ComplianceRecord not found",
        )
    _require_access(entity, current_user)
    return ComplianceRecordResponse(data=_to_data(entity))


@router.post(
    "",
    response_model=ComplianceRecordResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create compliance record",
    operation_id="createComplianceRecord",
    responses=error_responses(401, 403, 409, 422, 500),
)
async def create_compliance(
    request: ComplianceRecordCreateRequest,
    current_user=Depends(require_current_user),
    service: ComplianceRecordService = Depends(get_compliance_service),
):
    require_company_admin(current_user, request.companyId, action="write compliance for")

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
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message
        ) from exc
    return ComplianceRecordResponse(data=_to_data(created))


@router.patch(
    "/{id}",
    response_model=ComplianceRecordResponse,
    summary="Update compliance record",
    operation_id="updateComplianceRecord",
    responses=error_responses(401, 403, 404, 422, 500),
)
async def update_compliance(
    id: str,
    request: ComplianceRecordUpdateRequest,
    current_user=Depends(require_current_user),
    service: ComplianceRecordService = Depends(get_compliance_service),
):
    existing = await service.get_by_id(id)
    if existing is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="ComplianceRecord not found",
        )
    require_company_admin(current_user, existing.company_id, action="write compliance for")

    target_company_id = request.companyId if request.companyId is not None else existing.company_id
    if str(target_company_id) != str(existing.company_id):
        # Presun záznamu na inu firmu vyzaduje opravnenie v cielovej firme.
        require_company_admin(current_user, target_company_id, action="write compliance for")

    updated_entity = ComplianceRecordEntity(
        company_id=target_company_id,
        regulation_type=request.regulationType
        if request.regulationType is not None
        else existing.regulation_type,
        document_ref=request.documentRef
        if request.documentRef is not None
        else existing.document_ref,
        valid_until=request.validUntil if request.validUntil is not None else existing.valid_until,
        notes=request.notes if request.notes is not None else existing.notes,
        status=ComplianceRecordStatus(request.status)
        if request.status is not None
        else existing.status,
    )
    try:
        result = await service.update(id, updated_entity)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except ValidationDomainError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message
        ) from exc
    return ComplianceRecordResponse(data=_to_data(result))


@router.delete(
    "/{id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    summary="Delete compliance record",
    operation_id="deleteComplianceRecord",
    responses=error_responses(401, 403, 404, 500),
)
async def delete_compliance(
    id: str,
    current_user=Depends(require_current_user),
    service: ComplianceRecordService = Depends(get_compliance_service),
):
    existing = await service.get_by_id(id)
    if existing is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="ComplianceRecord not found",
        )
    require_company_admin(current_user, existing.company_id, action="write compliance for")
    try:
        await service.delete(id)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
