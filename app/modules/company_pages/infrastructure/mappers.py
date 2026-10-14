"""company_pages infrastructure mappers."""

from uuid import UUID

from app.modules.company_pages.domain.entities import CompanyPage, CompanyPhoto
from app.modules.company_pages.domain.enums import CompanyPageStatus
from app.modules.company_pages.infrastructure.models import (
    CompanyPageModel,
    CompanyPhotoModel,
)


def _uuid(value) -> UUID | None:
    if value is None:
        return None
    return value if isinstance(value, UUID) else UUID(str(value))


def page_to_domain(model: CompanyPageModel) -> CompanyPage:
    return CompanyPage(
        id=_uuid(model.id),
        company_id=_uuid(model.company_id),
        slug=model.slug,
        status=CompanyPageStatus(model.status),
        display_name=model.display_name,
        tagline=model.tagline,
        about_short=model.about_short,
        about_long=model.about_long,
        services=model.services,
        specialization=model.specialization,
        certifications=model.certifications,
        opening_hours=model.opening_hours,
        languages=model.languages,
        categories=model.categories,
        area=model.area,
        public_email=model.public_email,
        public_phone=model.public_phone,
        public_website=model.public_website,
        seo_title=model.seo_title,
        seo_description=model.seo_description,
        published_at=model.published_at,
        created_at=model.created_at,
        created_by_user_id=_uuid(model.created_by_user_id),
        updated_at=model.updated_at,
        updated_by_user_id=_uuid(model.updated_by_user_id),
    )


def page_to_model(entity: CompanyPage) -> CompanyPageModel:
    return CompanyPageModel(
        id=str(entity.id),
        company_id=str(entity.company_id),
        slug=entity.slug,
        status=entity.status.value,
        display_name=entity.display_name,
        tagline=entity.tagline,
        about_short=entity.about_short,
        about_long=entity.about_long,
        services=entity.services,
        specialization=entity.specialization,
        certifications=entity.certifications,
        opening_hours=entity.opening_hours,
        languages=entity.languages,
        categories=entity.categories,
        area=entity.area,
        public_email=entity.public_email,
        public_phone=entity.public_phone,
        public_website=entity.public_website,
        seo_title=entity.seo_title,
        seo_description=entity.seo_description,
        published_at=entity.published_at,
        created_at=entity.created_at,
        created_by_user_id=str(entity.created_by_user_id) if entity.created_by_user_id else None,
        updated_at=entity.updated_at,
        updated_by_user_id=str(entity.updated_by_user_id) if entity.updated_by_user_id else None,
    )


def photo_to_domain(model: CompanyPhotoModel) -> CompanyPhoto:
    return CompanyPhoto(
        id=_uuid(model.id),
        company_id=_uuid(model.company_id),
        file_url=model.file_url,
        caption=model.caption,
        alt_text=model.alt_text,
        position=model.position or 0,
        is_primary=bool(model.is_primary),
        created_at=model.created_at,
        created_by_user_id=_uuid(model.created_by_user_id),
        updated_at=model.updated_at,
        updated_by_user_id=_uuid(model.updated_by_user_id),
    )


def photo_to_model(entity: CompanyPhoto) -> CompanyPhotoModel:
    return CompanyPhotoModel(
        id=str(entity.id),
        company_id=str(entity.company_id),
        file_url=entity.file_url,
        caption=entity.caption,
        alt_text=entity.alt_text,
        position=entity.position,
        is_primary=entity.is_primary,
        created_at=entity.created_at,
        created_by_user_id=str(entity.created_by_user_id) if entity.created_by_user_id else None,
        updated_at=entity.updated_at,
        updated_by_user_id=str(entity.updated_by_user_id) if entity.updated_by_user_id else None,
    )
