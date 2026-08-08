"""inquiries API router."""

from fastapi import APIRouter, Depends, HTTPException, status as http_status

from app.shared.domain.exceptions import NotFoundDomainError, ValidationDomainError

from ..application.services import InquiryService
from ..domain.entities import InquiryEntity
from ..domain.enums import InquiryStatus
from .dependencies import get_inquiries_service
from .schemas import (
    InquiryCreateRequest,
    InquiryData,
    InquiryResponse,
    InquiryUpdateRequest,
    PaginatedInquirysResponse,
    PaginationMeta,
)

router = APIRouter(prefix="/inquiries", tags=["inquiries"])


def _to_data(entity: InquiryEntity) -> InquiryData:
    return InquiryData(
        id=entity.id,
        listingId=entity.listing_id,
        companyId=entity.company_id,
        message=entity.message,
        contactEmail=entity.contact_email,
        contactPhone=entity.contact_phone,
        status=entity.status.value,
        createdAt=entity.created_at,
        updatedAt=entity.updated_at,
    )


@router.get("/", response_model=PaginatedInquirysResponse)
async def list_inquiries(page: int = 1, limit: int = 20, service: InquiryService = Depends(get_inquiries_service)):
    items = await service.list_all(page, limit)
    total = await service.count_all()
    return PaginatedInquirysResponse(items=[_to_data(e) for e in items], meta=PaginationMeta(page=page, pageSize=limit, total=total))


@router.get("/{id}", response_model=InquiryResponse)
async def get_inquirie(id: str, service: InquiryService = Depends(get_inquiries_service)):
    entity = await service.get_by_id(id)
    if entity is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Inquiry not found")
    return InquiryResponse(data=_to_data(entity))


@router.post("/", response_model=InquiryResponse, status_code=http_status.HTTP_201_CREATED)
async def create_inquirie(request: InquiryCreateRequest, service: InquiryService = Depends(get_inquiries_service)):
    entity = InquiryEntity(
        listing_id=request.listingId,
        company_id=request.companyId,
        message=request.message,
        contact_email=request.contactEmail,
        contact_phone=request.contactPhone,
    )
    try:
        created = await service.create(entity)
    except ValidationDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc
    return InquiryResponse(data=_to_data(created))


@router.put("/{id}", response_model=InquiryResponse)
async def update_inquirie(id: str, request: InquiryUpdateRequest, service: InquiryService = Depends(get_inquiries_service)):
    existing = await service.get_by_id(id)
    if existing is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Inquiry not found")
    updated_entity = InquiryEntity(
        listing_id=request.listingId if request.listingId is not None else existing.listing_id,
        company_id=request.companyId if request.companyId is not None else existing.company_id,
        message=request.message if request.message is not None else existing.message,
        contact_email=request.contactEmail if request.contactEmail is not None else existing.contact_email,
        contact_phone=request.contactPhone if request.contactPhone is not None else existing.contact_phone,
        status=InquiryStatus(request.status) if request.status is not None else existing.status,
    )
    try:
        result = await service.update(id, updated_entity)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except ValidationDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc
    return InquiryResponse(data=_to_data(result))


@router.delete("/{id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_inquirie(id: str, service: InquiryService = Depends(get_inquiries_service)):
    try:
        await service.delete(id)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
