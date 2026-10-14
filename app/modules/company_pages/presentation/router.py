"""company_pages private API router (tenant editor).

Verejná firemná stránka je projekciou kanonických firemných údajov; kanonickým
zdrojom ostáva modul ``companies``. Tento router spravuje len údaje špecifické
pre verejnú prezentáciu (o nás, verejné kontakty, galéria, stav publikovania).

Autorizácia:
* čítanie (GET) — člen firmy (alebo platform admin)
* zápis (PUT/POST/PATCH/DELETE) — tenant admin firmy (owner/admin) alebo platform admin
"""

from __future__ import annotations

import contextlib
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.presentation.dependencies import get_company_repo
from app.modules.company_pages.application.services import (
    CompanyPageService,
    CompanyPhotoService,
)
from app.modules.company_pages.application.slug import slugify
from app.modules.company_pages.presentation.dependencies import (
    get_company_page_service,
    get_company_photo_service,
)
from app.modules.company_pages.presentation.mappers import to_page_data, to_photo_data
from app.modules.company_pages.presentation.schemas import (
    CompanyPagePhotoCreateRequest,
    CompanyPagePhotosResponse,
    CompanyPagePhotoUpdateRequest,
    CompanyPageReorderRequest,
    CompanyPageResponse,
    CompanyPageUpsertRequest,
    SlugAvailableResponse,
)
from app.shared.application.side_effects import write_audit
from app.shared.domain.exceptions import NotFoundDomainError
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import (
    current_user_id,
    require_company_admin,
    require_company_member,
)
from app.shared.presentation.error_schemas import error_responses

router = APIRouter(prefix="/companies", tags=["company-pages"])

_CAMEL_TO_SNAKE = {
    "displayName": "display_name",
    "tagline": "tagline",
    "aboutShort": "about_short",
    "aboutLong": "about_long",
    "services": "services",
    "specialization": "specialization",
    "certifications": "certifications",
    "openingHours": "opening_hours",
    "languages": "languages",
    "categories": "categories",
    "area": "area",
    "publicEmail": "public_email",
    "publicPhone": "public_phone",
    "publicWebsite": "public_website",
    "seoTitle": "seo_title",
    "seoDescription": "seo_description",
}


async def _get_company_or_404(company_repo, company_id):
    company = await company_repo.get_by_id(company_id)
    if company is None:
        raise NotFoundDomainError("Firma neexistuje.")
    return company


def _fields_from_payload(payload: CompanyPageUpsertRequest) -> dict:
    raw = payload.model_dump(exclude_unset=True)
    fields: dict = {}
    if "slug" in raw:
        fields["slug"] = raw["slug"]
    for camel, snake in _CAMEL_TO_SNAKE.items():
        if camel in raw:
            value = raw[camel]
            fields[snake] = str(value) if value is not None else None
    return fields


def _slug_source(payload: CompanyPageUpsertRequest, company) -> str | None:
    if payload.displayName:
        return payload.displayName
    return getattr(company, "trading_name", None) or getattr(company, "legal_name", None)


@router.get(
    "/{company_id}/page",
    response_model=CompanyPageResponse,
    responses=error_responses(401, 403, 404, 500),
)
async def get_company_page(
    company_id: UUID,
    current_user=Depends(require_current_user),
    company_repo=Depends(get_company_repo),
    service: CompanyPageService = Depends(get_company_page_service),
):
    """Vráti editor dáta stránky (alebo prázdny koncept pre novú firmu)."""
    require_company_member(current_user, company_id, action="view this company page")
    await _get_company_or_404(company_repo, company_id)
    page = await service.get_by_company_id(company_id)
    return CompanyPageResponse(data=to_page_data(page, company_id))


@router.put(
    "/{company_id}/page",
    response_model=CompanyPageResponse,
    responses=error_responses(401, 403, 404, 409, 422, 500),
)
async def upsert_company_page(
    company_id: UUID,
    payload: CompanyPageUpsertRequest,
    current_user=Depends(require_current_user),
    company_repo=Depends(get_company_repo),
    service: CompanyPageService = Depends(get_company_page_service),
    session: AsyncSession = Depends(get_db_session),
):
    """Vytvorí alebo aktualizuje verejnú stránku (koncept)."""
    require_company_admin(current_user, company_id)
    company = await _get_company_or_404(company_repo, company_id)
    actor = current_user_id(current_user)
    page = await service.upsert(
        company_id=company_id,
        actor_user_id=actor,
        base_slug_source=_slug_source(payload, company),
        fields=_fields_from_payload(payload),
    )
    with contextlib.suppress(Exception):
        await write_audit(
            session=session,
            actor_user_id=actor,
            action="company_page.upserted",
            target_type="company_page",
            target_id=page.id,
            details=f"companyId={company_id}; slug={page.slug}",
        )
    return CompanyPageResponse(data=to_page_data(page, company_id))


@router.post(
    "/{company_id}/page/publish",
    response_model=CompanyPageResponse,
    responses=error_responses(401, 403, 404, 422, 500),
)
async def publish_company_page(
    company_id: UUID,
    current_user=Depends(require_current_user),
    company_repo=Depends(get_company_repo),
    service: CompanyPageService = Depends(get_company_page_service),
    session: AsyncSession = Depends(get_db_session),
):
    """Zverejní stránku. Vyžaduje overenú firmu a vyplnené povinné polia."""
    require_company_admin(current_user, company_id)
    company = await _get_company_or_404(company_repo, company_id)
    actor = current_user_id(current_user)
    page = await service.publish(
        company_id=company_id,
        company_status=getattr(company, "status", None),
        actor_user_id=actor,
    )
    with contextlib.suppress(Exception):
        await write_audit(
            session=session,
            actor_user_id=actor,
            action="company_page.published",
            target_type="company_page",
            target_id=page.id,
            details=f"companyId={company_id}; slug={page.slug}",
        )
    return CompanyPageResponse(data=to_page_data(page, company_id))


@router.post(
    "/{company_id}/page/unpublish",
    response_model=CompanyPageResponse,
    responses=error_responses(401, 403, 404, 500),
)
async def unpublish_company_page(
    company_id: UUID,
    current_user=Depends(require_current_user),
    company_repo=Depends(get_company_repo),
    service: CompanyPageService = Depends(get_company_page_service),
    session: AsyncSession = Depends(get_db_session),
):
    """Stiahne stránku z verejného prístupu (stav -> draft)."""
    require_company_admin(current_user, company_id)
    await _get_company_or_404(company_repo, company_id)
    actor = current_user_id(current_user)
    page = await service.unpublish(company_id=company_id, actor_user_id=actor)
    with contextlib.suppress(Exception):
        await write_audit(
            session=session,
            actor_user_id=actor,
            action="company_page.unpublished",
            target_type="company_page",
            target_id=page.id,
            details=f"companyId={company_id}",
        )
    return CompanyPageResponse(data=to_page_data(page, company_id))


@router.get(
    "/{company_id}/page/slug-available",
    response_model=SlugAvailableResponse,
    responses=error_responses(401, 403, 500),
)
async def check_slug_available(
    company_id: UUID,
    slug: str = Query(..., min_length=1, max_length=120),
    current_user=Depends(require_current_user),
    service: CompanyPageService = Depends(get_company_page_service),
):
    """Overí dostupnosť adresy (slug) pre danú firmu."""
    require_company_member(current_user, company_id, action="check slug for")
    available, reason = await service.slug_available(slug, company_id)
    return SlugAvailableResponse(slug=slugify(slug), available=available, reason=reason)


# ─────────────────────────────────────────────────────────────
# FOTOGALÉRIA
# ─────────────────────────────────────────────────────────────


@router.get(
    "/{company_id}/photos",
    response_model=CompanyPagePhotosResponse,
    responses=error_responses(401, 403, 500),
)
async def list_company_photos(
    company_id: UUID,
    current_user=Depends(require_current_user),
    service: CompanyPhotoService = Depends(get_company_photo_service),
):
    require_company_member(current_user, company_id, action="view photos of")
    photos = await service.list(company_id)
    return CompanyPagePhotosResponse(
        items=[to_photo_data(p) for p in photos],
        meta={"total": len(photos)},
    )


@router.post(
    "/{company_id}/photos",
    response_model=CompanyPagePhotosResponse,
    responses=error_responses(401, 403, 404, 422, 500),
)
async def add_company_photo(
    company_id: UUID,
    payload: CompanyPagePhotoCreateRequest,
    current_user=Depends(require_current_user),
    company_repo=Depends(get_company_repo),
    service: CompanyPhotoService = Depends(get_company_photo_service),
    session: AsyncSession = Depends(get_db_session),
):
    require_company_admin(current_user, company_id)
    await _get_company_or_404(company_repo, company_id)
    actor = current_user_id(current_user)
    photo = await service.add(
        company_id=company_id,
        file_url=payload.fileUrl,
        caption=payload.caption,
        alt_text=payload.altText,
        actor_user_id=actor,
    )
    with contextlib.suppress(Exception):
        await write_audit(
            session=session,
            actor_user_id=actor,
            action="company_photo.added",
            target_type="company_photo",
            target_id=photo.id,
            details=f"companyId={company_id}",
        )
    photos = await service.list(company_id)
    return CompanyPagePhotosResponse(
        items=[to_photo_data(p) for p in photos],
        meta={"total": len(photos)},
    )


@router.patch(
    "/{company_id}/photos/{photo_id}",
    response_model=CompanyPagePhotosResponse,
    responses=error_responses(401, 403, 404, 422, 500),
)
async def update_company_photo(
    company_id: UUID,
    photo_id: UUID,
    payload: CompanyPagePhotoUpdateRequest,
    current_user=Depends(require_current_user),
    service: CompanyPhotoService = Depends(get_company_photo_service),
):
    require_company_admin(current_user, company_id)
    actor = current_user_id(current_user)
    raw = payload.model_dump(exclude_unset=True)
    await service.update(
        company_id=company_id,
        photo_id=photo_id,
        caption=raw.get("caption"),
        alt_text=raw.get("altText"),
        actor_user_id=actor,
    )
    photos = await service.list(company_id)
    return CompanyPagePhotosResponse(
        items=[to_photo_data(p) for p in photos],
        meta={"total": len(photos)},
    )


@router.delete(
    "/{company_id}/photos/{photo_id}",
    response_model=CompanyPagePhotosResponse,
    responses=error_responses(401, 403, 404, 500),
)
async def delete_company_photo(
    company_id: UUID,
    photo_id: UUID,
    current_user=Depends(require_current_user),
    service: CompanyPhotoService = Depends(get_company_photo_service),
    session: AsyncSession = Depends(get_db_session),
):
    require_company_admin(current_user, company_id)
    actor = current_user_id(current_user)
    await service.delete(company_id=company_id, photo_id=photo_id)
    with contextlib.suppress(Exception):
        await write_audit(
            session=session,
            actor_user_id=actor,
            action="company_photo.deleted",
            target_type="company_photo",
            target_id=photo_id,
            details=f"companyId={company_id}",
        )
    photos = await service.list(company_id)
    return CompanyPagePhotosResponse(
        items=[to_photo_data(p) for p in photos],
        meta={"total": len(photos)},
    )


@router.put(
    "/{company_id}/photos/order",
    response_model=CompanyPagePhotosResponse,
    responses=error_responses(401, 403, 404, 422, 500),
)
async def reorder_company_photos(
    company_id: UUID,
    payload: CompanyPageReorderRequest,
    current_user=Depends(require_current_user),
    service: CompanyPhotoService = Depends(get_company_photo_service),
):
    require_company_admin(current_user, company_id)
    actor = current_user_id(current_user)
    photos = await service.reorder(
        company_id=company_id,
        ordered_ids=payload.orderedIds,
        actor_user_id=actor,
    )
    return CompanyPagePhotosResponse(
        items=[to_photo_data(p) for p in photos],
        meta={"total": len(photos)},
    )


@router.post(
    "/{company_id}/photos/{photo_id}/primary",
    response_model=CompanyPagePhotosResponse,
    responses=error_responses(401, 403, 404, 500),
)
async def set_primary_company_photo(
    company_id: UUID,
    photo_id: UUID,
    current_user=Depends(require_current_user),
    service: CompanyPhotoService = Depends(get_company_photo_service),
):
    require_company_admin(current_user, company_id)
    actor = current_user_id(current_user)
    photos = await service.set_primary(
        company_id=company_id, photo_id=photo_id, actor_user_id=actor
    )
    return CompanyPagePhotosResponse(
        items=[to_photo_data(p) for p in photos],
        meta={"total": len(photos)},
    )
