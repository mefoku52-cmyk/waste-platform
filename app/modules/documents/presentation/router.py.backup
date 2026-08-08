"""documents API router."""

from fastapi import APIRouter, Depends, HTTPException, status as http_status

from app.shared.domain.exceptions import NotFoundDomainError, ValidationDomainError

from ..application.services import DocumentService
from ..domain.entities import DocumentEntity
from ..domain.enums import DocumentStatus
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
        status=entity.status.value,
        createdAt=entity.created_at,
        updatedAt=entity.updated_at,
    )


@router.get("/", response_model=PaginatedDocumentsResponse)
async def list_documents(page: int = 1, limit: int = 20, service: DocumentService = Depends(get_documents_service)):
    items = await service.list_all(page, limit)
    total = await service.count_all()
    return PaginatedDocumentsResponse(items=[_to_data(e) for e in items], meta=PaginationMeta(page=page, pageSize=limit, total=total))


@router.get("/{id}", response_model=DocumentResponse)
async def get_document(id: str, service: DocumentService = Depends(get_documents_service)):
    entity = await service.get_by_id(id)
    if entity is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentResponse(data=_to_data(entity))


@router.post("/", response_model=DocumentResponse, status_code=http_status.HTTP_201_CREATED)
async def create_document(request: DocumentCreateRequest, service: DocumentService = Depends(get_documents_service)):
    entity = DocumentEntity(
        title=request.title,
        document_type=request.documentType,
        file_url=request.fileUrl,
        company_id=request.companyId,
        listing_id=request.listingId,
    )
    try:
        created = await service.create(entity)
    except ValidationDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc
    return DocumentResponse(data=_to_data(created))


@router.put("/{id}", response_model=DocumentResponse)
async def update_document(id: str, request: DocumentUpdateRequest, service: DocumentService = Depends(get_documents_service)):
    existing = await service.get_by_id(id)
    if existing is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Document not found")
    updated_entity = DocumentEntity(
        title=request.title if request.title is not None else existing.title,
        document_type=request.documentType if request.documentType is not None else existing.document_type,
        file_url=request.fileUrl if request.fileUrl is not None else existing.file_url,
        company_id=request.companyId if request.companyId is not None else existing.company_id,
        listing_id=request.listingId if request.listingId is not None else existing.listing_id,
        status=DocumentStatus(request.status) if request.status is not None else existing.status,
    )
    try:
        result = await service.update(id, updated_entity)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except ValidationDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc
    return DocumentResponse(data=_to_data(result))


@router.delete("/{id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_document(id: str, service: DocumentService = Depends(get_documents_service)):
    try:
        await service.delete(id)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
