"""inquiries API router."""

from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status

from app.shared.application.side_effects import notify_company_members, write_audit
from app.shared.domain.exceptions import (
    ForbiddenDomainError,
    NotFoundDomainError,
    ValidationDomainError,
)
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import (
    current_user_id,
    is_platform_admin,
    membership_company_ids,
    require_company_member,
)
from app.shared.presentation.error_schemas import error_responses

from ..application.services import InquiryService
from ..domain.entities import InquiryEntity
from ..domain.enums import InquiryStatus
from .dependencies import get_inquiries_service
from .schemas import (
    InquiryCreateRequest,
    InquiryData,
    InquiryResponse,
    InquiryStatusUpdateRequest,
    InquiryUpdateRequest,
    PaginatedInquiriesResponse,
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
        status=entity.status,
        createdAt=entity.created_at,
        updatedAt=entity.updated_at,
        listingTitle=listing_title,
    )


def _user_company_ids(current_user) -> list:
    """Company IDs clenstva — jedina zdielana definicia."""
    return membership_company_ids(current_user)


async def _require_inquiry_participant(service: InquiryService, entity, current_user) -> None:
    """Inquiry smie vidiet/upravovat platform admin, kupujuca firma alebo predavajuci."""
    if is_platform_admin(current_user):
        return
    if str(entity.company_id) in {str(x) for x in _user_company_ids(current_user)}:
        return
    if await service.seller_owns_inquiry(str(entity.id), _user_company_ids(current_user)):
        return
    raise ForbiddenDomainError("You do not have access to this inquiry")


@router.get(
    "",
    response_model=PaginatedInquiriesResponse,
    responses=error_responses(401, 403, 422, 500),
)
async def list_inquiries(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    current_user=Depends(require_current_user),
    service: InquiryService = Depends(get_inquiries_service),
):
    # Neomezeny zoznam vsetkych dopytov je platform-admin operacia.
    if not is_platform_admin(current_user):
        raise ForbiddenDomainError("Platform admin access required")

    items = await service.list_all(page, pageSize)
    total = await service.count_all()
    return PaginatedInquiriesResponse(
        items=[_to_data(e) for e in items],
        meta=PaginationMeta(page=page, pageSize=pageSize, total=total),
    )


@router.get(
    "/received",
    response_model=PaginatedInquiriesResponse,
    responses=error_responses(401, 403, 422, 500),
)
async def list_received_inquiries(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    current_user=Depends(require_current_user),
    service: InquiryService = Depends(get_inquiries_service),
):
    company_ids = _user_company_ids(current_user)
    rows = await service.list_received(page, pageSize, seller_company_ids=company_ids)
    total = await service.count_received(seller_company_ids=company_ids)
    return PaginatedInquiriesResponse(
        items=[_to_data(e, title) for e, title in rows],
        meta=PaginationMeta(page=page, pageSize=pageSize, total=total),
    )


@router.get(
    "/sent",
    response_model=PaginatedInquiriesResponse,
    responses=error_responses(401, 403, 422, 500),
)
async def list_sent_inquiries(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    current_user=Depends(require_current_user),
    service: InquiryService = Depends(get_inquiries_service),
):
    company_ids = _user_company_ids(current_user)
    rows = await service.list_sent(page, pageSize, company_ids=company_ids)
    total = await service.count_sent(company_ids=company_ids)
    return PaginatedInquiriesResponse(
        items=[_to_data(e, title) for e, title in rows],
        meta=PaginationMeta(page=page, pageSize=pageSize, total=total),
    )


@router.get(
    "/{id}",
    response_model=InquiryResponse,
    responses=error_responses(401, 403, 404, 500),
)
async def get_inquiry(
    id: str,
    current_user=Depends(require_current_user),
    service: InquiryService = Depends(get_inquiries_service),
):
    entity = await service.get_by_id(id)
    if entity is None:
        raise NotFoundDomainError(f"Inquiry {id} not found")
    await _require_inquiry_participant(service, entity, current_user)
    return InquiryResponse(data=_to_data(entity))


@router.post(
    "",
    response_model=InquiryResponse,
    status_code=http_status.HTTP_201_CREATED,
    responses=error_responses(401, 403, 409, 422, 500),
)
async def create_inquiry(
    request: InquiryCreateRequest,
    current_user=Depends(require_current_user),
    service: InquiryService = Depends(get_inquiries_service),
    session=Depends(get_db_session),
):
    # Dopyt sa vytvara v mene firmy, ktorej je user clenom.
    require_company_member(current_user, request.companyId, action="send inquiries for")

    from sqlalchemy import text

    listing_row = (
        await session.execute(
            text("SELECT company_id FROM listings WHERE id = :id"),
            {"id": str(request.listingId)},
        )
    ).first()
    if listing_row and str(listing_row[0]) == str(request.companyId):
        raise HTTPException(status_code=400, detail="Nemozes poslat dopyt na vlastnu ponuku.")

    now = datetime.now()
    entity = InquiryEntity(
        id=uuid4(),
        listing_id=request.listingId,
        company_id=request.companyId,
        message=request.message,
        contact_email=request.contactEmail,
        contact_phone=request.contactPhone,
        status=InquiryStatus.OPEN,
        created_at=now,
        updated_at=now,
        created_by_user_id=None,
        updated_by_user_id=None,
    )
    created = await service.create(entity)

    try:
        actor = current_user_id(current_user)
        await write_audit(
            session=session,
            actor_user_id=actor,
            action="inquiry.created",
            target_type="inquiry",
            target_id=created.id,
            details=f"listing={created.listing_id}",
        )

        from app.modules.companies.infrastructure.models import CompanyModel
        from app.modules.listings.infrastructure.models import ListingsModel

        listing = await session.get(ListingsModel, UUID(str(created.listing_id)))
        seller_cid = getattr(listing, "company_id", None)
        listing_title = getattr(listing, "title", None)
        seller_email = None
        if seller_cid is not None:
            company = await session.get(CompanyModel, str(seller_cid))
            seller_email = getattr(company, "email", None)

        email_lines = [
            "Nový dopyt k ponuke" + (f": {listing_title}" if listing_title else "") + ".",
            "",
            f"E-mail kupujúceho: {created.contact_email}",
        ]
        if created.contact_phone:
            email_lines.append(f"Telefón: {created.contact_phone}")
        email_lines.extend(["", "Správa:", created.message or ""])

        await notify_company_members(
            session=session,
            company_id=seller_cid,
            title="Nový dopyt k ponuke",
            message=(created.message or "")[:500],
            notif_type="inquiry_received",
            related_entity_id=created.id,
            exclude_user_id=actor,
            email_body="\n".join(email_lines),
            reply_to=created.contact_email,
            fallback_email=seller_email,
        )
    except Exception:
        pass  # best-effort: never break caller

    return InquiryResponse(data=_to_data(created))


@router.patch(
    "/{id}/status",
    response_model=InquiryResponse,
    responses=error_responses(401, 403, 404, 409, 422, 500),
)
async def update_inquiry_status(
    id: str,
    request: InquiryStatusUpdateRequest,
    current_user=Depends(require_current_user),
    service: InquiryService = Depends(get_inquiries_service),
    session=Depends(get_db_session),
):
    company_ids = {str(x) for x in _user_company_ids(current_user)}

    if request.status not in (
        InquiryStatus.OPEN,
        InquiryStatus.ANSWERED,
        InquiryStatus.CLOSED,
    ):
        raise ValidationDomainError("Invalid inquiry status transition target")

    try:
        result = await service.update_status_as_seller(
            id,
            request.status,
            seller_company_ids=list(company_ids),
        )
    except NotFoundDomainError:
        raise
    except ValidationDomainError:
        raise

    try:
        from app.shared.application.side_effects import notify_company_members

        t = str(getattr(request.status, "value", request.status)).lower()
        if t in ("answered", "closed"):
            await notify_company_members(
                session=session,
                company_id=result.company_id,
                title="Dopyt aktualizovany",
                message=f"Vas dopyt k ponuke bol oznaceny ako: {t}",
                notif_type="inquiry_updated",
                related_entity_id=result.id,
            )
    except Exception:
        pass  # best-effort: never break caller

    return InquiryResponse(data=_to_data(result))


@router.patch(
    "/{id}",
    response_model=InquiryResponse,
    responses=error_responses(401, 403, 404, 409, 422, 500),
)
async def update_inquiry(
    id: str,
    request: InquiryUpdateRequest,
    current_user=Depends(require_current_user),
    service: InquiryService = Depends(get_inquiries_service),
):
    existing = await service.get_by_id(id)
    if existing is None:
        raise NotFoundDomainError(f"Inquiry {id} not found")

    await _require_inquiry_participant(service, existing, current_user)

    target_company_id = request.companyId if request.companyId is not None else existing.company_id
    # Prepis firmy dopytu je mozny len na firmu, ktorej je user clenom.
    require_company_member(current_user, target_company_id, action="reassign inquiries for")

    updated_entity = InquiryEntity(
        listing_id=request.listingId if request.listingId is not None else existing.listing_id,
        company_id=target_company_id,
        message=request.message if request.message is not None else existing.message,
        contact_email=request.contactEmail
        if request.contactEmail is not None
        else existing.contact_email,
        contact_phone=request.contactPhone
        if request.contactPhone is not None
        else existing.contact_phone,
        status=request.status if request.status is not None else existing.status,
        created_at=existing.created_at,
        updated_at=existing.updated_at,
        created_by_user_id=existing.created_by_user_id,
        updated_by_user_id=getattr(existing, "updated_by_user_id", None),
    )
    result = await service.update(id, updated_entity)
    return InquiryResponse(data=_to_data(result))


@router.delete(
    "/{id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    responses=error_responses(401, 403, 404, 500),
)
async def delete_inquiry(
    id: str,
    current_user=Depends(require_current_user),
    service: InquiryService = Depends(get_inquiries_service),
):
    existing = await service.get_by_id(id)
    if existing is None:
        raise NotFoundDomainError(f"Inquiry {id} not found")
    await _require_inquiry_participant(service, existing, current_user)
    await service.delete(id)
