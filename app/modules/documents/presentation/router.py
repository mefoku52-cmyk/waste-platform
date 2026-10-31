"""documents API router."""

from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status

from app.shared.domain.exceptions import NotFoundDomainError
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import is_platform_admin, membership_company_ids
from app.shared.presentation.error_schemas import error_responses

from ..application.services import DocumentService
from ..domain.entities import DocumentEntity
from .dependencies import get_documents_service
from .schemas import (
    DocumentCreateRequest,
    DocumentData,
    DocumentResponse,
    DocumentUpdateRequest,
    PaginatedDocumentsResponse,
    PaginationMeta,
)

router = APIRouter(prefix="/documents", tags=["documents"])


def _to_data(entity: DocumentEntity) -> DocumentData:
    return DocumentData(
        id=entity.id,
        title=entity.title,
        documentType=entity.document_type,
        fileUrl=entity.file_url,
        companyId=entity.company_id,
        listingId=entity.listing_id,
        status=entity.status,
        createdAt=entity.created_at,
        updatedAt=entity.updated_at,
    )


def _allowed_company_ids(current_user) -> set:
    ids = set()
    for m in current_user.memberships or []:
        cid = m.get("companyId") if isinstance(m, dict) else getattr(m, "companyId", None)
        if cid is not None:
            ids.add(cid)
    return ids


def _ensure_document_access(entity: DocumentEntity, current_user) -> None:
    from app.shared.domain.exceptions import ForbiddenDomainError

    allowed_company_ids = _allowed_company_ids(current_user)
    if entity.company_id not in allowed_company_ids:
        raise ForbiddenDomainError("You do not have access to this document")


@router.get(
    "",
    response_model=PaginatedDocumentsResponse,
    responses=error_responses(401, 403, 422, 500),
)
async def list_documents(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    limit: int | None = Query(default=None, ge=1, le=100, include_in_schema=False),
    current_user=Depends(require_current_user),
    service: DocumentService = Depends(get_documents_service),
):
    effective_page_size = limit or pageSize

    if is_platform_admin(current_user):
        items = await service.list_all(page, effective_page_size)
        total = await service.count_all()
    else:
        company_ids = membership_company_ids(current_user)
        items = await service.list_by_company_ids(company_ids, page, effective_page_size)
        total = await service.count_by_company_ids(company_ids)
    return PaginatedDocumentsResponse(
        items=[_to_data(e) for e in items],
        meta=PaginationMeta(page=page, pageSize=effective_page_size, total=total),
    )


@router.get(
    "/{id}",
    response_model=DocumentResponse,
    responses=error_responses(401, 403, 404, 500),
)
async def get_document(
    id: str,
    current_user=Depends(require_current_user),
    service: DocumentService = Depends(get_documents_service),
):
    entity = await service.get_by_id(id)
    if entity is None:
        raise NotFoundDomainError(f"Document {id} not found")
    if not is_platform_admin(current_user):
        # Moderation/approval status does not change tenant ownership. Public
        # document sharing, if needed, must use a separate explicitly public route.
        _ensure_document_access(entity, current_user)

    return DocumentResponse(data=_to_data(entity))


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=http_status.HTTP_201_CREATED,
    responses=error_responses(401, 403, 409, 422, 500),
)
async def create_document(
    request: DocumentCreateRequest,
    current_user=Depends(require_current_user),
    service: DocumentService = Depends(get_documents_service),
):
    allowed_company_ids = _allowed_company_ids(current_user)
    if request.companyId not in allowed_company_ids:
        from app.shared.domain.exceptions import ForbiddenDomainError

        raise ForbiddenDomainError("You do not have access to this company")

    entity = DocumentEntity(
        title=request.title,
        document_type=request.documentType,
        file_url=request.fileUrl,
        company_id=request.companyId,
        listing_id=request.listingId,
    )
    created = await service.create(entity)
    return DocumentResponse(data=_to_data(created))


@router.patch(
    "/{id}",
    response_model=DocumentResponse,
    responses=error_responses(401, 403, 404, 409, 422, 500),
)
async def update_document(
    id: str,
    request: DocumentUpdateRequest,
    current_user=Depends(require_current_user),
    service: DocumentService = Depends(get_documents_service),
):
    existing = await service.get_by_id(id)
    if existing is None:
        raise NotFoundDomainError(f"Document {id} not found")

    platform_admin = is_platform_admin(current_user)
    if not platform_admin:
        _ensure_document_access(existing, current_user)

    from app.shared.domain.exceptions import ForbiddenDomainError

    if request.status is not None and not platform_admin:
        raise ForbiddenDomainError("Only platform administrators can change document status")

    target_company_id = request.companyId if request.companyId is not None else existing.company_id
    if not platform_admin and target_company_id not in _allowed_company_ids(current_user):
        from app.shared.domain.exceptions import ForbiddenDomainError

        raise ForbiddenDomainError("You do not have access to this company")

    updated_entity = DocumentEntity(
        title=request.title if request.title is not None else existing.title,
        document_type=request.documentType
        if request.documentType is not None
        else existing.document_type,
        file_url=request.fileUrl if request.fileUrl is not None else existing.file_url,
        company_id=target_company_id,
        listing_id=request.listingId if request.listingId is not None else existing.listing_id,
        status=request.status if request.status is not None else existing.status,
    )
    result = await service.update(id, updated_entity)
    return DocumentResponse(data=_to_data(result))


@router.delete(
    "/{id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    responses=error_responses(401, 403, 404, 500),
)
async def delete_document(
    id: str,
    current_user=Depends(require_current_user),
    service: DocumentService = Depends(get_documents_service),
):
    entity = await service.get_by_id(id)
    if entity is None:
        raise NotFoundDomainError(f"Document {id} not found")
    if not is_platform_admin(current_user):
        _ensure_document_access(entity, current_user)
    await service.delete(id)
