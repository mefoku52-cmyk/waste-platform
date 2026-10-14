"""company_pages public API router (no auth — verejné firemné stránky).

Bezpečnostný model:

* Zverejnené sú len stránky so stavom ``published``. Koncept/odpublikovaná
  stránka vracia 404 (rovnako ako neexistujúca — ne prezrádzame existenciu).
* Verejné obrázky sa neobsluhujú cez krátkodobé podpísané URL (tie by po
  expirácii rozbili verejnú stránku). Namiesto toho je stabilný endpoint
  ``/public/company-pages/{slug}/assets/{file_id}``, ktorý vydá súbor len ak
  patrí zverejnenej firme (galéria, logo alebo obrázok zverejnenej ponuky).
* Nikdy nevraciame interné firemné ID ani neverejné kontakty.
"""

from __future__ import annotations

import mimetypes
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.presentation.dependencies import get_company_repo
from app.modules.company_pages.presentation.dependencies import (
    get_company_page_service,
    get_photo_repo,
)
from app.modules.company_pages.presentation.schemas import (
    PublicCompanyInfo,
    PublicCompanyListing,
    PublicCompanyPageResponse,
    PublicCompanyPhoto,
    PublicCompanyReview,
    PublicSitemapEntry,
    PublicSitemapResponse,
)
from app.modules.company_reviews.presentation.dependencies import (
    get_company_review_service,
)
from app.modules.uploads.application.storage import (
    UPLOAD_ROOT,
    sanitize_file_id,
)
from app.shared.domain.exceptions import NotFoundDomainError
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.error_schemas import error_responses

public_router = APIRouter(prefix="/public", tags=["public-company-pages"])

_MAX_PUBLIC_LISTINGS = 24
_UPLOAD_URL_PREFIX = "/api/v1/uploads/"


def _file_id_of(url: str | None) -> str | None:
    """Vytiahne ``file_id`` z uloženej upload URL (``.../uploads/<file_id>``)."""
    if not url:
        return None
    tail = str(url).rstrip("/").split("/")[-1].split("?")[0]
    return sanitize_file_id(tail)


def _asset_url(slug: str, file_id: str) -> str:
    return f"/api/v1/public/company-pages/{slug}/assets/{file_id}"


async def _load_published_page(slug: str, service):
    page = await service.get_by_slug(slug)
    if page is None or str(getattr(page.status, "value", page.status)) != "published":
        raise NotFoundDomainError("Verejná stránka neexistuje.")
    return page


@public_router.get(
    "/company-pages",
    response_model=PublicSitemapResponse,
    responses=error_responses(500),
)
async def list_public_company_pages(
    page_service=Depends(get_company_page_service),
):
    """Zoznam zverejnených verejných stránok (slug + updatedAt) — pre sitemap.

    Zámerne NEobsahuje rozpracované/odpublikované stránky.
    """
    rows = await page_service.list_published_slugs()
    items = [PublicSitemapEntry(slug=slug, updatedAt=updated) for slug, updated in rows]
    return PublicSitemapResponse(items=items, meta={"total": len(items)})


@public_router.get(
    "/company-pages/{slug}",
    response_model=PublicCompanyPageResponse,
    responses=error_responses(404, 500),
)
async def get_public_company_page(
    slug: str,
    page_service=Depends(get_company_page_service),
    company_repo=Depends(get_company_repo),
    photo_repo=Depends(get_photo_repo),
    review_service=Depends(get_company_review_service),
    session: AsyncSession = Depends(get_db_session),
):
    page = await _load_published_page(slug, page_service)
    company = await company_repo.get_by_id(page.company_id)
    if company is None:
        raise NotFoundDomainError("Verejná stránka neexistuje.")

    display_name = (
        (page.display_name or "").strip()
        or getattr(company, "trading_name", None)
        or getattr(company, "legal_name", None)
        or ""
    )

    photos = await photo_repo.list_by_company(company.id)
    public_photos: list[PublicCompanyPhoto] = []
    for p in photos:
        fid = _file_id_of(p.file_url)
        if not fid:
            continue
        public_photos.append(
            PublicCompanyPhoto(
                url=_asset_url(slug, fid),
                caption=p.caption,
                altText=p.alt_text or p.caption,
                position=p.position,
                isPrimary=bool(p.is_primary),
            )
        )

    logo_fid = _file_id_of(getattr(company, "logo_url", None))

    from app.modules.listings.infrastructure.models import ListingsModel

    company_uuid = uuid.UUID(str(company.id))
    stmt = (
        select(ListingsModel)
        .where(ListingsModel.company_id == company_uuid)
        .where(ListingsModel.status == "published")
        .order_by(ListingsModel.created_at.desc())
        .limit(_MAX_PUBLIC_LISTINGS)
    )
    rows = (await session.execute(stmt)).scalars().all()
    public_listings: list[PublicCompanyListing] = []
    for r in rows:
        image_fid = _file_id_of(getattr(r, "image_url", None))
        public_listings.append(
            PublicCompanyListing(
                id=str(r.id),
                title=r.title,
                materialType=getattr(r, "material_type", None),
                quantity=getattr(r, "quantity", None),
                unit=getattr(r, "unit", None),
                price=getattr(r, "price", None),
                currency=getattr(r, "currency", None),
                location=getattr(r, "location", None),
                condition=getattr(r, "condition", None),
                imageUrl=_asset_url(slug, image_fid) if image_fid else None,
            )
        )

    status_value = str(getattr(company.status, "value", company.status))

    # Schválené recenzie + agregát (verejná časť).
    summary = await review_service.public_summary(company.id)
    public_reviews = [
        PublicCompanyReview(
            id=str(r.id),
            rating=r.rating,
            title=r.title,
            body=r.body,
            createdAt=r.created_at,
        )
        for r in summary["items"]
    ]

    return PublicCompanyPageResponse(
        slug=slug,
        publishedAt=page.published_at,
        displayName=display_name,
        tagline=page.tagline,
        aboutShort=page.about_short,
        aboutLong=page.about_long,
        services=page.services,
        specialization=page.specialization,
        certifications=page.certifications,
        openingHours=page.opening_hours,
        languages=page.languages,
        categories=page.categories,
        area=page.area,
        publicEmail=page.public_email,
        publicPhone=page.public_phone,
        publicWebsite=page.public_website,
        seoTitle=page.seo_title,
        seoDescription=page.seo_description,
        company=PublicCompanyInfo(
            displayName=display_name,
            legalName=getattr(company, "legal_name", None),
            companyType=str(getattr(company.company_type, "value", company.company_type)),
            city=getattr(company, "city", None),
            countryCode=getattr(company, "country_code", None),
            verified=status_value == "verified",
            sellerCapability=bool(getattr(company, "seller_capability", False)),
            buyerCapability=bool(getattr(company, "buyer_capability", False)),
            logisticsCapability=bool(getattr(company, "logistics_capability", False)),
            logoUrl=_asset_url(slug, logo_fid) if logo_fid else None,
        ),
        photos=public_photos,
        listings=public_listings,
        ratingAverage=summary["average"],
        ratingCount=summary["count"],
        reviews=public_reviews,
    )


@public_router.get(
    "/company-pages/{slug}/assets/{file_id}",
    responses=error_responses(400, 404, 500),
)
async def get_public_company_asset(
    slug: str,
    file_id: str,
    page_service=Depends(get_company_page_service),
    company_repo=Depends(get_company_repo),
    photo_repo=Depends(get_photo_repo),
    session: AsyncSession = Depends(get_db_session),
):
    """Vydá obrázok verejne, ale len ak patrí zverejnenej firme (bez podpisu)."""
    safe = sanitize_file_id(file_id)
    if safe is None:
        raise HTTPException(status_code=400, detail="Invalid file id")

    page = await _load_published_page(slug, page_service)
    company = await company_repo.get_by_id(page.company_id)
    if company is None:
        raise NotFoundDomainError("Verejná stránka neexistuje.")

    allowed = False

    logo_fid = _file_id_of(getattr(company, "logo_url", None))
    if logo_fid == safe:
        allowed = True

    if not allowed:
        photos = await photo_repo.list_by_company(company.id)
        if any(_file_id_of(p.file_url) == safe for p in photos):
            allowed = True

    if not allowed:
        from app.modules.listings.infrastructure.models import ListingsModel

        company_uuid = uuid.UUID(str(company.id))
        stmt = (
            select(ListingsModel.image_url)
            .where(ListingsModel.company_id == company_uuid)
            .where(ListingsModel.status == "published")
        )
        urls = (await session.execute(stmt)).scalars().all()
        if any(_file_id_of(u) == safe for u in urls):
            allowed = True

    if not allowed:
        # 404 (nie 403) — ne prezrádzame, že súbor existuje inde.
        raise NotFoundDomainError("Súbor neexistuje.")

    path = UPLOAD_ROOT / safe
    if not Path(path).is_file():
        raise NotFoundDomainError("Súbor neexistuje.")

    media_type, _ = mimetypes.guess_type(str(path))
    response = FileResponse(path, media_type=media_type or "application/octet-stream")
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "public, max-age=86400"
    response.headers["Content-Security-Policy"] = "default-src 'none'; sandbox"
    return response
