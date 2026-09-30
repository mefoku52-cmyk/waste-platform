from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.modules.companies.application.rpo import lookup_ico
from app.modules.companies.presentation.dependencies import (
    get_create_company_service,
    get_get_company_service,
    get_list_companies_service,
    get_set_subscription_tier_service,
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
    SubscriptionTierUpdateRequest,
)
from app.shared.application.side_effects import write_audit
from app.shared.domain.exceptions import ForbiddenDomainError
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import (
    require_current_user,
)
from app.shared.presentation.authorization import (
    is_platform_admin,
    membership_company_ids,
    require_company_admin,
    require_company_member,
)
from app.shared.presentation.error_schemas import error_responses


def _is_admin(current_user) -> bool:
    """Platform admin. Deleguje na spolocnu definiciu opravnenia.

    Pozn.: tenant rola `admin` (firemne clenstvo) NIE je platform admin.
    """
    return is_platform_admin(current_user)


router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/rpo-check")
async def rpo_check(ico: str, current_user=Depends(require_current_user)):
    return lookup_ico(ico)


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
    if target in admin_only and not _is_admin(current_user):
        from app.shared.domain.exceptions import ForbiddenDomainError

        raise ForbiddenDomainError("Overenie firmy môže vykonať len administrátor.")

    try:
        dto = await service.execute(
            legal_name=payload.legalName,
            trading_name=payload.tradingName,
            registration_number=payload.registrationNumber,
            tax_identifier=payload.taxIdentifier,
            vat_identifier=getattr(payload, "vatIdentifier", None),
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
    except ValueError as exc:
        if str(exc) == "ICO_NOT_FOUND":
            raise HTTPException(status_code=400, detail="IČO v RPO neexistuje") from exc
        raise
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
    require_company_member(current_user, company_id, action="access")
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
    require_company_admin(current_user, company_id)
    dto = await service.execute(
        company_id=company_id,
        legal_name=payload.legalName,
        trading_name=payload.tradingName,
        tax_identifier=payload.taxIdentifier,
        vat_identifier=getattr(payload, "vatIdentifier", None),
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
    else:
        # Neadministrativny prechod (napr. verification_submitted) vyzaduje
        # tenant opravnenie v ramci danej firmy.
        require_company_admin(current_user, company_id)

    dto = await service.execute(
        company_id=company_id,
        to_status=payload.toStatus,
        actor_user_id=current_user.user.id,
    )
    actor = getattr(getattr(current_user, "user", None), "id", None)
    import contextlib

    with contextlib.suppress(Exception):
        await write_audit(
            session=session,
            actor_user_id=actor,
            action="company.status_changed",
            target_type="company",
            target_id=company_id,
            details=f"toStatus={payload.toStatus}",
        )
    try:
        from app.shared.application.side_effects import notify_company_members

        tl = str(payload.toStatus).lower()
        if tl == "verified":
            await notify_company_members(
                session=session,
                company_id=company_id,
                title="Firma overena",
                message="Vasa firma bola overena administratorom.",
                notif_type="company_verified",
                related_entity_id=company_id,
                exclude_user_id=actor,
            )
        elif tl == "rejected":
            await notify_company_members(
                session=session,
                company_id=company_id,
                title="Firma zamietnuta",
                message="Overenie vasej firmy bolo zamietnute.",
                notif_type="company_rejected",
                related_entity_id=company_id,
                exclude_user_id=actor,
            )
    except Exception:
        pass
    return CompanyResponse(data=to_company_data(dto))


@router.patch(
    "/{company_id}/subscription-tier",
    response_model=CompanyResponse,
    responses=error_responses(401, 403, 404, 422, 500),
)
async def set_company_subscription_tier(
    company_id: UUID,
    payload: SubscriptionTierUpdateRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_set_subscription_tier_service),
    session=Depends(get_db_session),
):
    """Platform-admin-only: set a company subscription tier."""
    if not _is_admin(current_user):
        raise ForbiddenDomainError("Subscription tier may only be changed by a platform admin.")

    dto = await service.execute(
        company_id=company_id,
        tier=payload.tier,
        actor_user_id=current_user.user.id,
    )

    await write_audit(
        session=session,
        actor_user_id=current_user.user.id,
        action="company.subscription_tier_changed",
        target_type="company",
        target_id=str(company_id),
        details=f"tier={payload.tier.value}",
    )

    return CompanyResponse(data=to_company_data(dto))


# ─────────────────────────────────────────────────────────────
# CONTACT REVEAL
# ─────────────────────────────────────────────────────────────
# Kontakty su skryte dokym medzi firmami neexistuje dokonceny
# vztah (inquiry answered/closed). Vlastna firma vidi vzdy.


async def _has_revealed_relationship(
    *,
    session,
    my_company_ids: list[str],
    target_company_id: str,
) -> tuple[bool, str]:
    """Vrati (revealed, reason).

    Reveal nastane ak:
    - som vlastnik cielovej firmy
    - existuje inquiry medzi mojou firmou a cielovou firmou
      so statusom 'answered' alebo 'closed'
    """
    target = str(target_company_id)

    # 1. Vlastna firma
    if target in {str(x) for x in my_company_ids}:
        return True, "own_company"

    if not my_company_ids:
        return False, "no_membership"

    # 2. Existuje inquiry kde my sme buyer (company_id) a seller je target company?
    #    alebo my sme seller a buyer je target?
    from sqlalchemy import text

    my_ids = [str(x) for x in my_company_ids]

    # 2a. Ja ako buyer, target ako seller (cez listing.company_id)
    try:
        r = await session.execute(
            text(
                """
                SELECT i.status
                FROM inquiries i
                JOIN listings l ON l.id = i.listing_id
                WHERE i.company_id = ANY(:my_ids)
                  AND l.company_id = :target
                  AND i.status IN ('answered', 'closed')
                LIMIT 1
                """
            ),
            {"my_ids": my_ids, "target": target},
        )
        if r.first() is not None:
            return True, "inquiry_answered"
    except Exception:
        # ANY(:array) nemusi fungovat na vsetkych dialektoch - fallback cez IN
        placeholders = ",".join(f":c{i}" for i in range(len(my_ids)))
        params = {f"c{i}": v for i, v in enumerate(my_ids)}
        params["target"] = target
        r = await session.execute(
            text(
                f"""
                SELECT i.status
                FROM inquiries i
                JOIN listings l ON l.id = i.listing_id
                WHERE i.company_id IN ({placeholders})
                  AND l.company_id = :target
                  AND i.status IN ('answered', 'closed')
                LIMIT 1
                """
            ),
            params,
        )
        if r.first() is not None:
            return True, "inquiry_answered"

    # 2b. Ja ako seller (moje listings), target ako buyer (i.company_id)
    placeholders = ",".join(f":m{i}" for i in range(len(my_ids)))
    params2 = {f"m{i}": v for i, v in enumerate(my_ids)}
    params2["target"] = target
    r2 = await session.execute(
        text(
            f"""
            SELECT i.status
            FROM inquiries i
            JOIN listings l ON l.id = i.listing_id
            WHERE l.company_id IN ({placeholders})
              AND i.company_id = :target
              AND i.status IN ('answered', 'closed')
            LIMIT 1
            """
        ),
        params2,
    )
    if r2.first() is not None:
        return True, "inquiry_answered"

    return False, "no_relationship"


class CompanyContactsResponse(BaseModel):
    companyId: UUID
    revealed: bool
    reason: str
    email: str | None = None
    phone: str | None = None
    websiteUrl: str | None = None


@router.get(
    "/{company_id}/contacts",
    response_model=CompanyContactsResponse,
    responses=error_responses(401, 403, 404, 500),
)
async def get_company_contacts(
    company_id: UUID,
    current_user=Depends(require_current_user),
    service=Depends(get_get_company_service),
    session=Depends(get_db_session),
):
    """Vrati kontakty firmy.

    - Vlastna firma -> vzdy vsetko
    - Existuje inquiry (answered/closed) medzi firmami -> vsetko
    - Inak -> revealed=false, kontakty=null
    """
    company_ids = membership_company_ids(current_user)
    revealed, reason = await _has_revealed_relationship(
        session=session,
        my_company_ids=company_ids,
        target_company_id=str(company_id),
    )

    if not revealed:
        return CompanyContactsResponse(
            companyId=company_id,
            revealed=False,
            reason=reason,
        )

    dto = await service.execute(company_id)
    return CompanyContactsResponse(
        companyId=company_id,
        revealed=True,
        reason=reason,
        email=dto.email,
        phone=dto.phone,
        websiteUrl=dto.website_url,
    )
