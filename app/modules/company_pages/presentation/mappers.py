"""company_pages presentation mappers (domain entity -> API schema)."""

from __future__ import annotations

from app.modules.company_pages.domain.entities import (
    CompanyPage,
    CompanyPhoto,
    missing_publish_requirements,
)
from app.modules.company_pages.presentation.schemas import (
    CompanyPageData,
    CompanyPhotoData,
)


def _s(value) -> str | None:
    return None if value is None else str(value)


def to_page_data(page: CompanyPage | None, company_id) -> CompanyPageData:
    """Mapovať entitu na DTO; ``page`` môže byť None (editor pre novú stránku)."""
    if page is None:
        return CompanyPageData(
            id=None,
            companyId=str(company_id),
            slug="",
            status="draft",
            exists=False,
            displayName=None,
            tagline=None,
            aboutShort=None,
            aboutLong=None,
            services=None,
            specialization=None,
            certifications=None,
            openingHours=None,
            languages=None,
            categories=None,
            area=None,
            publicEmail=None,
            publicPhone=None,
            publicWebsite=None,
            seoTitle=None,
            seoDescription=None,
            publishedAt=None,
            createdAt=None,
            updatedAt=None,
            missingForPublish=missing_publish_requirements(
                CompanyPage(company_id=company_id, slug="placeholder")
            ),
        )
    return CompanyPageData(
        id=_s(page.id),
        companyId=str(page.company_id),
        slug=page.slug,
        status=str(getattr(page.status, "value", page.status)),
        exists=True,
        displayName=page.display_name,
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
        publishedAt=page.published_at,
        createdAt=page.created_at,
        updatedAt=page.updated_at,
        missingForPublish=missing_publish_requirements(page),
    )


def to_photo_data(photo: CompanyPhoto) -> CompanyPhotoData:
    return CompanyPhotoData(
        id=str(photo.id),
        fileUrl=photo.file_url,
        caption=photo.caption,
        altText=photo.alt_text,
        position=photo.position,
        isPrimary=bool(photo.is_primary),
        createdAt=photo.created_at,
    )
