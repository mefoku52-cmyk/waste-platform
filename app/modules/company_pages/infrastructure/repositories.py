"""company_pages repository implementations."""

from __future__ import annotations

import uuid

from sqlalchemy import delete as sql_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.company_pages.domain.entities import CompanyPage, CompanyPhoto
from app.modules.company_pages.domain.repositories import (
    CompanyPageRepository,
    CompanyPhotoRepository,
)
from app.modules.company_pages.infrastructure.mappers import (
    page_to_domain,
    page_to_model,
    photo_to_domain,
    photo_to_model,
)
from app.modules.company_pages.infrastructure.models import (
    CompanyPageModel,
    CompanyPhotoModel,
)


def _as_uuid(value):
    if value is None:
        return None
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


class CompanyPageRepositoryImpl(CompanyPageRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_company_id(self, company_id) -> CompanyPage | None:
        stmt = select(CompanyPageModel).where(
            CompanyPageModel.company_id == str(_as_uuid(company_id))
        )
        model = (await self.session.execute(stmt)).scalar_one_or_none()
        return page_to_domain(model) if model else None

    async def get_by_id(self, page_id) -> CompanyPage | None:
        model = await self.session.get(CompanyPageModel, str(_as_uuid(page_id)))
        return page_to_domain(model) if model else None

    async def get_by_slug(self, slug: str) -> CompanyPage | None:
        stmt = select(CompanyPageModel).where(CompanyPageModel.slug == slug)
        model = (await self.session.execute(stmt)).scalar_one_or_none()
        return page_to_domain(model) if model else None

    async def list_slugs(self) -> list[str]:
        result = await self.session.execute(select(CompanyPageModel.slug))
        return [row[0] for row in result.all()]

    async def list_published_slugs(self) -> list[tuple[str, object]]:
        stmt = (
            select(CompanyPageModel.slug, CompanyPageModel.updated_at)
            .where(CompanyPageModel.status == "published")
            .order_by(CompanyPageModel.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def create(self, page: CompanyPage) -> CompanyPage:
        model = page_to_model(page)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return page_to_domain(model)

    async def update(self, page: CompanyPage) -> CompanyPage:
        model = await self.session.get(CompanyPageModel, str(_as_uuid(page.id)))
        if model is None:
            raise ValueError("Company page not found")
        model.slug = page.slug
        model.status = page.status.value
        model.display_name = page.display_name
        model.tagline = page.tagline
        model.about_short = page.about_short
        model.about_long = page.about_long
        model.services = page.services
        model.specialization = page.specialization
        model.certifications = page.certifications
        model.opening_hours = page.opening_hours
        model.languages = page.languages
        model.categories = page.categories
        model.area = page.area
        model.public_email = page.public_email
        model.public_phone = page.public_phone
        model.public_website = page.public_website
        model.seo_title = page.seo_title
        model.seo_description = page.seo_description
        model.published_at = page.published_at
        model.updated_at = page.updated_at
        model.updated_by_user_id = str(page.updated_by_user_id) if page.updated_by_user_id else None
        await self.session.commit()
        await self.session.refresh(model)
        return page_to_domain(model)


class CompanyPhotoRepositoryImpl(CompanyPhotoRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_company(self, company_id) -> list[CompanyPhoto]:
        stmt = (
            select(CompanyPhotoModel)
            .where(CompanyPhotoModel.company_id == str(_as_uuid(company_id)))
            .order_by(CompanyPhotoModel.position.asc(), CompanyPhotoModel.created_at.asc())
        )
        models = (await self.session.execute(stmt)).scalars().all()
        return [photo_to_domain(m) for m in models]

    async def get_by_id(self, photo_id) -> CompanyPhoto | None:
        model = await self.session.get(CompanyPhotoModel, str(_as_uuid(photo_id)))
        return photo_to_domain(model) if model else None

    async def count_by_company(self, company_id) -> int:
        stmt = (
            select(func.count())
            .select_from(CompanyPhotoModel)
            .where(CompanyPhotoModel.company_id == str(_as_uuid(company_id)))
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def create(self, photo: CompanyPhoto) -> CompanyPhoto:
        model = photo_to_model(photo)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return photo_to_domain(model)

    async def update(self, photo: CompanyPhoto) -> CompanyPhoto:
        model = await self.session.get(CompanyPhotoModel, str(_as_uuid(photo.id)))
        if model is None:
            raise ValueError("Company photo not found")
        model.file_url = photo.file_url
        model.caption = photo.caption
        model.alt_text = photo.alt_text
        model.position = photo.position
        model.is_primary = photo.is_primary
        model.updated_at = photo.updated_at
        model.updated_by_user_id = (
            str(photo.updated_by_user_id) if photo.updated_by_user_id else None
        )
        await self.session.commit()
        await self.session.refresh(model)
        return photo_to_domain(model)

    async def delete(self, photo_id) -> None:
        await self.session.execute(
            sql_delete(CompanyPhotoModel).where(CompanyPhotoModel.id == str(_as_uuid(photo_id)))
        )
        await self.session.commit()
