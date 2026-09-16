from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.modules.companies.presentation.dependencies import (
    get_create_company_service,
    get_get_company_service,
    get_list_companies_service,
    get_transition_company_status_service,
    get_update_company_service,
)
from app.modules.companies.presentation.mappers import to_company_data
from app.modules.companies.presentation.schemas import (
    CompanyCreateRequest,
    CompanyResponse,
    CompanyStatusTransitionRequest,
    CompanyUpdateRequest,
    PaginatedCompaniesResponse,
    PaginationMeta,
)
from app.shared.application.side_effects import write_audit
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import (
    require_current_user,
)
from app.shared.presentation.error_schemas import error_responses


def _is_admin(current_user) -> bool:
    from app.core.config import settings

    codes = list(
        getattr(current_user, "roleCodes", None) or getattr(current_user, "role_codes", None) or []
    )
    codes = [str(c).lower() for c in codes]
    u = getattr(current_user, "user", None)
    email = ""
    if u is not None:
        email = str(getattr(u, "email", "") or "").lower()
    else:
        email = str(getattr(current_user, "email", "") or "").lower()
    raw = getattr(settings, "PLATFORM_ADMIN_EMAILS", None) or "admin@cmep.dev"
    admins = {x.strip().lower() for x in str(raw).split(",") if x.strip()}
    return email in admins or "admin" in codes or "platform_admin" in codes


router = APIRouter(prefix="/companies", tags=["companies"])


@router.get(
    "",
    response_model=PaginatedCompaniesResponse,
    responses=error_responses(401, 403, 422, 500),
)
async def list_companies(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=25, ge=1, le=100),
    status: str | None = None,
    companyType: str | None = None,
    sellerCapability: bool | None = None,
    buyerCapability: bool | None = None,
    logisticsCapability: bool | None = None,
    q: str | None = None,
    current_user=Depends(require_current_user),
    service=Depends(get_list_companies_service),
):
    if _is_admin(current_user):
        company_ids = None
    else:
        company_ids = [
            (m.get("companyId") if isinstance(m, dict) else getattr(m, "companyId", None))
            for m in (current_user.memberships or [])
        ]
        company_ids = [cid for cid in company_ids if cid is not None]
    items, total = await service.execute(
        status=status,
        company_type=companyType,
        seller_capability=sellerCapability,
        buyer_capability=buyerCapability,
        logistics_capability=logisticsCapability,
        q=q,
        page=page,
        page_size=pageSize,
        company_ids=company_ids,
    )
    return PaginatedCompaniesResponse(
        items=[to_company_data(item) for item in items],
        meta=PaginationMeta(page=page, pageSize=pageSize, total=total),
    )


@router.post(
    "",
    response_model=CompanyResponse,
    status_code=201,
    responses=error_responses(401, 403, 409, 422, 500),
)
async def create_company(
    payload: CompanyCreateRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_create_company_service),
):
    admin_only = {"verified", "rejected", "suspended", "inactive"}
    target = str(getattr(payload, "toStatus", "") or "").lower()
    if target in admin_only:
        roles = list(getattr(current_user, "roleCodes", None) or [])
        u = getattr(current_user, "user", None)
        email = (getattr(u, "email", None) if u is not None else None) or getattr(
            current_user, "email", None
        )
        is_admin = (
            "admin" in [str(r).lower() for r in roles]
            or "platform_admin" in [str(r).lower() for r in roles]
            or (email and str(email).lower() == "admin@cmep.dev")
        )
        if not is_admin:
            from app.shared.domain.exceptions import ForbiddenDomainError

            raise ForbiddenDomainError("Overenie firmy môže vykonať len administrátor.")

    dto = await service.execute(
        legal_name=payload.legalName,
        trading_name=payload.tradingName,
        registration_number=payload.registrationNumber,
        tax_identifier=payload.taxIdentifier,
        company_type=payload.companyType,
        email=payload.email,
        phone=payload.phone,
        website_url=str(payload.websiteUrl) if payload.websiteUrl else None,
        country_code=payload.countryCode,
        address_line_1=payload.addressLine1,
        address_line_2=payload.addressLine2,
        city=payload.city,
        postal_code=payload.postalCode,
        latitude=payload.latitude,
        longitude=payload.longitude,
        seller_capability=payload.sellerCapability,
        buyer_capability=payload.buyerCapability,
        logistics_capability=payload.logisticsCapability,
        actor_user_id=current_user.user.id,
    )
    return CompanyResponse(data=to_company_data(dto))


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    responses=error_responses(401, 403, 404, 500),
)
async def get_company(
    company_id: UUID,
    current_user=Depends(require_current_user),
    service=Depends(get_get_company_service),
):
    dto = await service.execute(company_id)
    return CompanyResponse(data=to_company_data(dto))


@router.patch(
    "/{company_id}",
    response_model=CompanyResponse,
    responses=error_responses(401, 403, 404, 409, 422, 500),
)
async def update_company(
    company_id: UUID,
    payload: CompanyUpdateRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_update_company_service),
):
    dto = await service.execute(
        company_id=company_id,
        legal_name=payload.legalName,
        trading_name=payload.tradingName,
        tax_identifier=payload.taxIdentifier,
        email=payload.email,
        phone=payload.phone,
        website_url=str(payload.websiteUrl) if payload.websiteUrl else None,
        address_line_1=payload.addressLine1,
        address_line_2=payload.addressLine2,
        city=payload.city,
        postal_code=payload.postalCode,
        latitude=payload.latitude,
        longitude=payload.longitude,
        actor_user_id=current_user.user.id,
    )
    return CompanyResponse(data=to_company_data(dto))


@router.patch(
    "/{company_id}/status",
    response_model=CompanyResponse,
    responses=error_responses(401, 403, 404, 409, 422, 500),
)
async def transition_company_status(
    company_id: UUID,
    payload: CompanyStatusTransitionRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_transition_company_status_service),
    session=Depends(get_db_session),
):
    from app.shared.domain.exceptions import ForbiddenDomainError

    target = str(getattr(payload, "toStatus", None) or getattr(payload, "to_status", "")).lower()
    admin_only = {"verified", "rejected", "suspended", "inactive"}

    if target in admin_only:
        if not _is_admin(current_user):
            raise ForbiddenDomainError("Overenie firmy moze vykonat len administrator platformy.")

    dto = await service.execute(
        company_id=company_id,
        to_status=payload.toStatus,
        actor_user_id=current_user.user.id,
    )
    try:
        actor = getattr(getattr(current_user, "user", None), "id", None)
        await write_audit(
            session=session,
            actor_user_id=actor,
            action="company.status_changed",
            target_type="company",
            target_id=company_id,
            details=f"toStatus={payload.toStatus}",
        )
    except Exception:
        pass
    return CompanyResponse(data=to_company_data(dto))
