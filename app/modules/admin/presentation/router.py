from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import (
    require_admin,
    require_current_user,
)

"""admin API router."""

import re

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy import func, or_, select

from app.shared.domain.exceptions import ForbiddenDomainError, ValidationDomainError
from app.shared.presentation.authorization import current_user_id, is_platform_admin
from app.shared.presentation.error_schemas import error_responses

from ..application.services import AdminAuditEntryService
from ..domain.entities import AdminAuditEntryEntity
from .dependencies import get_admin_service
from .schemas import (
    AdminAuditEntryCreateRequest,
    AdminAuditEntryData,
    AdminAuditEntryResponse,
    AdminCompaniesResponse,
    AdminCompanyDetailData,
    AdminCompanyDetailResponse,
    AdminCompanyListItem,
    AdminCompanyMembershipData,
    AdminCompanyPhotoData,
    PaginatedAdminAuditEntriesResponse,
    PaginationMeta,
)

router = APIRouter(prefix="/admin", tags=["admin-audit"])

_SENSITIVE_RE = re.compile(
    r"(?i)\b(token|secret|password|passwd|api[_-]?key|authorization|refresh[_-]?token|access[_-]?token)\b"
    r"\s*[:=]\s*([^\s;,]+)"
)
_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
_LONG_HEX_RE = re.compile(r"\b[a-f0-9]{32,}\b", re.IGNORECASE)


def _redact_details(details: str | None) -> str | None:
    if not details:
        return details
    redacted = _SENSITIVE_RE.sub(lambda m: f"{m.group(1)}=[REDACTED]", details)
    redacted = _JWT_RE.sub("[REDACTED]", redacted)
    return _LONG_HEX_RE.sub("[REDACTED]", redacted)


def _to_data(entity: AdminAuditEntryEntity, actor=None) -> AdminAuditEntryData:
    email = getattr(actor, "email", None) if actor is not None else None
    first = getattr(actor, "first_name", None) if actor is not None else None
    last = getattr(actor, "last_name", None) if actor is not None else None
    name = " ".join(x for x in (first, last) if x) or None
    return AdminAuditEntryData(
        id=entity.id,
        actorUserId=entity.actor_user_id,
        actorEmail=email,
        actorName=name,
        action=entity.action,
        targetType=entity.target_type,
        targetId=entity.target_id,
        details=_redact_details(entity.details),
        status=entity.status.value,
        createdAt=entity.created_at,
        updatedAt=entity.updated_at,
    )


async def _load_actors(session, entities) -> dict:
    ids = {str(e.actor_user_id) for e in entities if e.actor_user_id}
    if not ids:
        return {}
    from app.modules.users.infrastructure.models import UserModel

    rows = (await session.execute(select(UserModel).where(UserModel.id.in_(ids)))).scalars().all()
    return {str(u.id): u for u in rows}


@router.get(
    "",
    response_model=PaginatedAdminAuditEntriesResponse,
    summary="List current user's audit entries",
    operation_id="listCurrentUserAuditEntries",
)
async def list_admin(
    page: int = 1,
    limit: int = 20,
    current_user=Depends(require_current_user),
    service: AdminAuditEntryService = Depends(get_admin_service),
):
    uid = getattr(getattr(current_user, "user", None), "id", None) or getattr(
        current_user, "id", None
    )
    items = await service.list_by_actor(uid, page, limit)
    total = await service.count_by_actor(uid)
    return PaginatedAdminAuditEntriesResponse(
        items=[_to_data(e) for e in items],
        meta=PaginationMeta(page=page, pageSize=limit, total=total),
    )


@router.get(
    "/all",
    response_model=PaginatedAdminAuditEntriesResponse,
    summary="List all audit entries",
    operation_id="listAllAuditEntries",
)
async def list_all_admin(
    page: int = 1,
    limit: int = 20,
    current_user=Depends(require_admin),
    service: AdminAuditEntryService = Depends(get_admin_service),
    session=Depends(get_db_session),
):
    items = await service.list_all(page, limit)
    total = await service.count_all()
    actors = await _load_actors(session, items)
    return PaginatedAdminAuditEntriesResponse(
        items=[_to_data(e, actors.get(str(e.actor_user_id))) for e in items],
        meta=PaginationMeta(page=page, pageSize=limit, total=total),
    )


@router.get(
    "/stats",
    summary="Platform stats for admin dashboard",
)
async def admin_stats(
    current_user=Depends(require_admin),
    session=Depends(get_db_session),
):
    from sqlalchemy import text

    users = (await session.execute(text("SELECT COUNT(*) FROM users"))).scalar_one()
    listings = (await session.execute(text("SELECT COUNT(*) FROM listings"))).scalar_one()
    companies = (await session.execute(text("SELECT COUNT(*) FROM companies"))).scalar_one()
    pending = (
        await session.execute(
            text("SELECT COUNT(*) FROM companies WHERE status = 'verification_submitted'")
        )
    ).scalar_one()
    return {
        "total_users": int(users),
        "total_listings": int(listings),
        "total_companies": int(companies),
        "pending_verifications": int(pending),
    }


@router.get(
    "/users",
    summary="List users for admin dashboard",
)
async def admin_list_users(
    current_user=Depends(require_admin),
    session=Depends(get_db_session),
):
    from sqlalchemy import text

    from app.core.config import settings

    admin_emails = {
        item.strip().lower()
        for item in str(settings.PLATFORM_ADMIN_EMAILS or "").split(",")
        if item.strip()
    }

    rows = await session.execute(
        text(
            "SELECT id, email, first_name, last_name, status, last_login_at, created_at "
            "FROM users ORDER BY created_at DESC LIMIT 200"
        )
    )
    items = []
    for r in rows.mappings():
        email = str(r["email"] or "").lower()
        items.append(
            {
                "id": str(r["id"]),
                "email": r["email"],
                "firstName": r["first_name"],
                "lastName": r["last_name"],
                "status": r["status"],
                "lastLogin": r["last_login_at"].isoformat() if r["last_login_at"] else None,
                "createdAt": r["created_at"].isoformat() if r["created_at"] else None,
                "roleCodes": ["platform_admin"] if email in admin_emails else [],
            }
        )
    return {
        "items": items,
        "data": items,
        "meta": {"total": len(items)},
    }


@router.get(
    "/users/{user_id}/summary",
    summary="User summary — profil + pocty aktivit",
)
async def admin_user_summary(
    user_id: str,
    current_user=Depends(require_admin),
    session=Depends(get_db_session),
):
    from sqlalchemy import text

    # Profil
    row = (
        (
            await session.execute(
                text(
                    "SELECT id, email, first_name, last_name, status, "
                    "last_login_at, created_at, updated_at "
                    "FROM users WHERE id = :uid"
                ),
                {"uid": user_id},
            )
        )
        .mappings()
        .first()
    )

    if row is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Pocty aktivit
    counts = {}
    for label, query in [
        (
            "listings",
            "SELECT COUNT(*) FROM listings WHERE company_id IN "
            "(SELECT company_id FROM company_memberships WHERE user_id = :uid)",
        ),
        (
            "inquiries",
            "SELECT COUNT(*) FROM inquiries WHERE company_id IN "
            "(SELECT company_id FROM company_memberships WHERE user_id = :uid)",
        ),
        ("memberships", "SELECT COUNT(*) FROM company_memberships WHERE user_id = :uid"),
        ("activity_events", "SELECT COUNT(*) FROM activity_events WHERE actor_user_id = :uid"),
    ]:
        try:
            result = await session.execute(text(query), {"uid": user_id})
            counts[label] = int(result.scalar_one())
        except Exception:
            counts[label] = None

    return {
        "user": {
            "id": str(row["id"]),
            "email": row["email"],
            "firstName": row["first_name"],
            "lastName": row["last_name"],
            "status": row["status"],
            "lastLoginAt": row["last_login_at"].isoformat() if row["last_login_at"] else None,
            "createdAt": row["created_at"].isoformat() if row["created_at"] else None,
            "updatedAt": row["updated_at"].isoformat() if row["updated_at"] else None,
        },
        "counts": counts,
    }


@router.get(
    "/users/{user_id}/activity",
    summary="User activity — poslednych 100 eventov",
)
async def admin_user_activity(
    user_id: str,
    limit: int = 100,
    current_user=Depends(require_admin),
    session=Depends(get_db_session),
):
    from sqlalchemy import text

    limit = max(1, min(int(limit), 500))

    rows = (
        (
            await session.execute(
                text(
                    "SELECT id, event_type, company_id, listing_id, payload, created_at "
                    "FROM activity_events WHERE actor_user_id = :uid "
                    "ORDER BY created_at DESC LIMIT :lim"
                ),
                {"uid": user_id, "lim": limit},
            )
        )
        .mappings()
        .all()
    )

    items = [
        {
            "id": str(r["id"]),
            "eventType": r["event_type"],
            "companyId": r["company_id"],
            "listingId": r["listing_id"],
            "payload": r["payload"],
            "createdAt": r["created_at"].isoformat() if r["created_at"] else None,
        }
        for r in rows
    ]

    return {"items": items, "total": len(items)}


@router.get(
    "/companies",
    response_model=AdminCompaniesResponse,
    summary="List companies for platform admin",
    operation_id="adminListCompanies",
    responses=error_responses(401, 403, 422, 500),
)
async def admin_list_companies(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None, max_length=32),
    q: str | None = Query(default=None, max_length=200),
    current_user=Depends(require_admin),
    session=Depends(get_db_session),
):
    from app.modules.companies.infrastructure.models import CompanyModel
    from app.modules.company_pages.infrastructure.models import CompanyPhotoModel

    stmt = select(CompanyModel)
    if status:
        stmt = stmt.where(CompanyModel.status == status)
    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                CompanyModel.legal_name.ilike(like),
                CompanyModel.trading_name.ilike(like),
                CompanyModel.registration_number.ilike(like),
                CompanyModel.email.ilike(like),
            )
        )
    total = int(
        (
            await session.execute(select(func.count()).select_from(stmt.order_by(None).subquery()))
        ).scalar_one()
    )
    rows = (
        (
            await session.execute(
                stmt.order_by(CompanyModel.created_at.desc())
                .offset((page - 1) * pageSize)
                .limit(pageSize)
            )
        )
        .scalars()
        .all()
    )
    ids = [str(c.id) for c in rows]
    photo_counts: dict[str, int] = {}
    if ids:
        photo_rows = await session.execute(
            select(CompanyPhotoModel.company_id, func.count())
            .where(CompanyPhotoModel.company_id.in_(ids))
            .group_by(CompanyPhotoModel.company_id)
        )
        photo_counts = {str(cid): int(cnt) for cid, cnt in photo_rows.all()}

    items = [
        AdminCompanyListItem(
            id=str(c.id),
            status=str(c.status),
            legalName=c.legal_name,
            tradingName=c.trading_name,
            registrationNumber=c.registration_number,
            email=c.email,
            phone=c.phone,
            city=c.city,
            countryCode=c.country_code,
            subscriptionTier=c.subscription_tier,
            companyType=c.company_type,
            photoCount=photo_counts.get(str(c.id), 0),
            createdAt=c.created_at,
        )
        for c in rows
    ]
    return AdminCompaniesResponse(
        items=items,
        meta=PaginationMeta(page=page, pageSize=pageSize, total=total),
    )


@router.get(
    "/companies/{company_id}",
    response_model=AdminCompanyDetailResponse,
    summary="Company detail for platform admin",
    operation_id="adminGetCompany",
    responses=error_responses(401, 403, 404, 500),
)
async def admin_get_company(
    company_id: str,
    current_user=Depends(require_admin),
    session=Depends(get_db_session),
):
    import uuid as _uuid

    from app.modules.companies.infrastructure.models import CompanyModel
    from app.modules.company_memberships.infrastructure.models import (
        CompanyMembershipModel,
    )
    from app.modules.company_pages.infrastructure.models import (
        CompanyPageModel,
        CompanyPhotoModel,
    )
    from app.modules.inquiries.infrastructure.models import InquiryModel
    from app.modules.listings.infrastructure.models import ListingsModel
    from app.modules.users.infrastructure.models import UserModel

    company = await session.get(CompanyModel, str(company_id))
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    page_row = (
        (
            await session.execute(
                select(CompanyPageModel).where(CompanyPageModel.company_id == str(company.id))
            )
        )
        .scalars()
        .first()
    )
    photo_rows = (
        (
            await session.execute(
                select(CompanyPhotoModel)
                .where(CompanyPhotoModel.company_id == str(company.id))
                .order_by(
                    CompanyPhotoModel.position.asc(),
                    CompanyPhotoModel.created_at.asc(),
                )
            )
        )
        .scalars()
        .all()
    )
    membership_rows = (
        await session.execute(
            select(CompanyMembershipModel, UserModel)
            .outerjoin(UserModel, UserModel.id == CompanyMembershipModel.user_id)
            .where(CompanyMembershipModel.company_id == str(company.id))
            .order_by(CompanyMembershipModel.created_at.asc())
        )
    ).all()

    counts: dict[str, int] = {
        "photos": len(photo_rows),
        "memberships": len(membership_rows),
    }
    try:
        cid = _uuid.UUID(str(company.id))
        counts["listings"] = int(
            (
                await session.execute(
                    select(func.count())
                    .select_from(ListingsModel)
                    .where(ListingsModel.company_id == cid)
                )
            ).scalar_one()
        )
        counts["inquiries"] = int(
            (
                await session.execute(
                    select(func.count())
                    .select_from(InquiryModel)
                    .where(InquiryModel.company_id == cid)
                )
            ).scalar_one()
        )
    except (ValueError, TypeError):
        counts["listings"] = 0
        counts["inquiries"] = 0

    data = AdminCompanyDetailData(
        id=str(company.id),
        status=str(company.status),
        legalName=company.legal_name,
        tradingName=company.trading_name,
        registrationNumber=company.registration_number,
        taxIdentifier=company.tax_identifier,
        vatIdentifier=company.vat_identifier,
        email=company.email,
        phone=company.phone,
        websiteUrl=company.website_url,
        city=company.city,
        countryCode=company.country_code,
        addressLine1=company.address_line_1,
        addressLine2=company.address_line_2,
        postalCode=company.postal_code,
        subscriptionTier=company.subscription_tier,
        companyType=company.company_type,
        sellerCapability=bool(company.seller_capability),
        buyerCapability=bool(company.buyer_capability),
        logisticsCapability=bool(company.logistics_capability),
        verificationSubmittedAt=company.verification_submitted_at,
        verifiedAt=company.verified_at,
        rejectedAt=company.rejected_at,
        photoCount=len(photo_rows),
        createdAt=company.created_at,
        pageSlug=page_row.slug if page_row else None,
        pageStatus=str(page_row.status) if page_row else None,
        publicEmail=page_row.public_email if page_row else None,
        publicPhone=page_row.public_phone if page_row else None,
        counts=counts,
        memberships=[
            AdminCompanyMembershipData(
                userId=str(m.user_id),
                email=getattr(u, "email", None),
                firstName=getattr(u, "first_name", None),
                lastName=getattr(u, "last_name", None),
                role=str(m.membership_role),
                status=str(m.status),
                isPrimaryContact=bool(m.is_primary_contact),
            )
            for m, u in membership_rows
        ],
        photos=[
            AdminCompanyPhotoData(
                id=str(p.id),
                fileUrl=p.file_url,
                caption=p.caption,
                altText=p.alt_text,
                position=int(p.position or 0),
                isPrimary=bool(p.is_primary),
                createdAt=p.created_at,
            )
            for p in photo_rows
        ],
    )
    return AdminCompanyDetailResponse(data=data)


@router.get(
    "/{id}",
    response_model=AdminAuditEntryResponse,
    summary="Get audit entry by ID",
    operation_id="getAuditEntryById",
    responses=error_responses(401, 403, 404, 500),
)
async def get_admin(
    id: str,
    current_user=Depends(require_admin),
    service: AdminAuditEntryService = Depends(get_admin_service),
    session=Depends(get_db_session),
):
    entity = await service.get_by_id(id)
    if entity is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="AdminAuditEntry not found",
        )
    actors = await _load_actors(session, [entity])
    return AdminAuditEntryResponse(data=_to_data(entity, actors.get(str(entity.actor_user_id))))


@router.post(
    "",
    response_model=AdminAuditEntryResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create audit entry",
    operation_id="createAuditEntry",
    responses=error_responses(401, 403, 409, 422, 500),
)
async def create_admin(
    request: AdminAuditEntryCreateRequest,
    current_user=Depends(require_current_user),
    service: AdminAuditEntryService = Depends(get_admin_service),
):
    # Audit zaznam smie vytvorit platform admin, alebo user zaznam len o sebe.
    actor = current_user_id(current_user)
    if not is_platform_admin(current_user) and str(request.actorUserId) != str(actor):
        raise ForbiddenDomainError("You cannot create audit entries for another user")

    entity = AdminAuditEntryEntity(
        actor_user_id=request.actorUserId,
        action=request.action,
        target_type=request.targetType,
        target_id=request.targetId,
        details=request.details,
    )
    try:
        created = await service.create(entity)
    except ValidationDomainError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message
        ) from exc
    return AdminAuditEntryResponse(data=_to_data(created))
