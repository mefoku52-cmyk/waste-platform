"""inquiries API router."""

from fastapi import APIRouter, Depends, HTTPException, status as http_status
from app.shared.presentation.auth_dependencies import require_current_user

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
    InquiryStatusUpdateRequest,
    PaginatedInquirysResponse,
    PaginationMeta,
)

router = APIRouter(prefix="/inquiries", tags=["inquiries"])


def _to_data(entity: InquiryEntity, listing_title: str | None = None) -> InquiryData:
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
        listingTitle=listing_title,
    )


def _user_company_ids(current_user) -> list:
    ids = [
        (m.get("companyId") if isinstance(m, dict) else getattr(m, "companyId", None))
        for m in (current_user.memberships or [])
    ]
    return [cid for cid in ids if cid is not None]


@router.get("/", response_model=PaginatedInquirysResponse)
async def list_inquiries(page: int = 1, limit: int = 20, service: InquiryService = Depends(get_inquiries_service)):
    items = await service.list_all(page, limit)
    total = await service.count_all()
    return PaginatedInquirysResponse(items=[_to_data(e) for e in items], meta=PaginationMeta(page=page, pageSize=limit, total=total))


@router.get("/received", response_model=PaginatedInquirysResponse)
async def list_received_inquiries(
    page: int = 1,
    limit: int = 20,
    current_user=Depends(require_current_user),
    service: InquiryService = Depends(get_inquiries_service),
):
    company_ids = [
        (m.get("companyId") if isinstance(m, dict) else getattr(m, "companyId", None))
        for m in (current_user.memberships or [])
    ]
    company_ids = [cid for cid in company_ids if cid is not None]
    rows = await service.list_received(page, limit, seller_company_ids=company_ids)
    total = await service.count_received(seller_company_ids=company_ids)
    return PaginatedInquirysResponse(
        items=[_to_data(e, title) for e, title in rows],
        meta=PaginationMeta(page=page, pageSize=limit, total=total),
    )


@router.get("/sent", response_model=PaginatedInquirysResponse)
async def list_sent_inquiries(
    page: int = 1,
    limit: int = 20,
    current_user=Depends(require_current_user),
    service: InquiryService = Depends(get_inquiries_service),
):
    company_ids = [
        (m.get("companyId") if isinstance(m, dict) else getattr(m, "companyId", None))
        for m in (current_user.memberships or [])
    ]
    company_ids = [cid for cid in company_ids if cid is not None]
    rows = await service.list_sent(page, limit, company_ids=company_ids)
    total = await service.count_sent(company_ids=company_ids)
    return PaginatedInquirysResponse(
        items=[_to_data(e, title) for e, title in rows],
        meta=PaginationMeta(page=page, pageSize=limit, total=total),
    )


@router.get("/{id}", response_model=InquiryResponse)
async def get_inquiry(id: str, service: InquiryService = Depends(get_inquiries_service)):
    entity = await service.get_by_id(id)
    if entity is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Inquiry not found")
    return InquiryResponse(data=_to_data(entity))


@router.post("/", response_model=InquiryResponse, status_code=http_status.HTTP_201_CREATED)
async def create_inquiry(request: InquiryCreateRequest, service: InquiryService = Depends(get_inquiries_service)):
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


@router.patch("/{id}/status", response_model=InquiryResponse)
async def update_inquiry_status(
    id: str,
    request: InquiryStatusUpdateRequest,
    current_user=Depends(require_current_user),
    service: InquiryService = Depends(get_inquiries_service),
):
    """Predávajúci (vlastník listingu) zmení status dopytu: open|answered|closed."""
    from app.modules.listings.presentation.dependencies import get_listings_service
    # auth: memberships
    company_ids = {str(x) for x in _user_company_ids(current_user)}
    existing = await service.get_by_id(id)
    if existing is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Inquiry not found")
    # overenie cez listing – musí patriť mojej firme
    from app.modules.inquiries.presentation.dependencies import get_inquiries_service as _
    # listing lookup cez inquiries session nie; použijeme listings service z dependency injection nie je tu –
    # fallback: service layer check
    try:
        new_status = InquiryStatus(request.status)
    except ValueError:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid status")
    if new_status not in (InquiryStatus.OPEN, InquiryStatus.ANSWERED, InquiryStatus.CLOSED):
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid status")
    try:
        result = await service.update_status_as_seller(
            id, new_status, seller_company_ids=list(company_ids)
        )
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except ValidationDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=exc.message) from exc
    return InquiryResponse(data=_to_data(result))


@router.put("/{id}", response_model=InquiryResponse)
async def update_inquiry(id: str, request: InquiryUpdateRequest,
    InquiryStatusUpdateRequest, service: InquiryService = Depends(get_inquiries_service)):
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
async def delete_inquiry(id: str, service: InquiryService = Depends(get_inquiries_service)):
    try:
        await service.delete(id)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
