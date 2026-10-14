"""company_pages application services."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from app.modules.company_pages.application.slug import (
    is_valid_slug,
    slugify,
    unique_slug,
)
from app.modules.company_pages.domain.entities import (
    CompanyPage,
    CompanyPhoto,
    missing_publish_requirements,
)
from app.modules.company_pages.domain.enums import CompanyPageStatus
from app.modules.company_pages.domain.repositories import (
    CompanyPageRepository,
    CompanyPhotoRepository,
)
from app.shared.application.clock import Clock
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.domain.exceptions import (
    ConflictDomainError,
    NotFoundDomainError,
    ValidationDomainError,
)

# Kapacita galérie v prvej verzii (požadovaná kapacita, nie povinnosť).
MAX_PHOTOS = 10

# Firma musí byť overená, aby mohla zverejniť verejnú stránku.
PUBLISHABLE_COMPANY_STATUSES = frozenset({"verified"})

_EDITABLE_FIELDS = (
    "display_name",
    "tagline",
    "about_short",
    "about_long",
    "services",
    "specialization",
    "certifications",
    "opening_hours",
    "languages",
    "categories",
    "area",
    "public_email",
    "public_phone",
    "public_website",
    "seo_title",
    "seo_description",
)


class CompanyPageService:
    def __init__(
        self,
        repo: CompanyPageRepository,
        uuid_generator: UuidGenerator,
        clock: Clock,
    ):
        self.repo = repo
        self.uuid_generator = uuid_generator
        self.clock = clock

    async def get_by_company_id(self, company_id) -> CompanyPage | None:
        return await self.repo.get_by_company_id(company_id)

    async def get_by_slug(self, slug: str) -> CompanyPage | None:
        return await self.repo.get_by_slug(slug)

    async def list_published_slugs(self) -> list[tuple[str, object]]:
        """Zoznam zverejnených slugov (+ updated_at) pre sitemap/SEO."""
        return await self.repo.list_published_slugs()

    def blank_draft(self, company_id) -> CompanyPage:
        """Nová (neuložená) koncept-stránka pre editor, keď záznam ešte neexistuje."""
        return CompanyPage(
            company_id=company_id,
            slug="",
            status=CompanyPageStatus.DRAFT,
        )

    async def slug_available(self, slug: str, company_id=None) -> tuple[bool, str]:
        cleaned = slugify(slug)
        if not is_valid_slug(cleaned):
            return False, "invalid"
        existing = await self.repo.get_by_slug(cleaned)
        if existing is not None and (
            company_id is None or str(existing.company_id) != str(company_id)
        ):
            return False, "taken"
        return True, "available"

    async def upsert(
        self,
        *,
        company_id,
        actor_user_id,
        base_slug_source: str | None,
        fields: dict,
    ) -> CompanyPage:
        existing = await self.repo.get_by_company_id(company_id)
        slugs = await self.repo.list_slugs()

        requested_raw = fields.pop("slug", None)
        if requested_raw is not None:
            requested = slugify(requested_raw)
            if not is_valid_slug(requested):
                raise ValidationDomainError(
                    "Neplatná adresa stránky (slug): 3-80 znakov, len a-z, 0-9 a '-'."
                )
            if requested in slugs and (existing is None or existing.slug != requested):
                raise ConflictDomainError("Táto adresa stránky je už obsadená.")
            slug = requested
        elif existing is not None:
            slug = existing.slug
        else:
            base = slugify(base_slug_source) or ""
            if not is_valid_slug(base):
                base = "firma"
            slug = unique_slug(base, slugs)

        now = self.clock.now()

        if existing is None:
            page = CompanyPage(
                id=self.uuid_generator.new(),
                company_id=company_id,
                slug=slug,
                status=CompanyPageStatus.DRAFT,
                created_at=now,
                created_by_user_id=actor_user_id,
                updated_at=now,
                updated_by_user_id=actor_user_id,
            )
            for key in _EDITABLE_FIELDS:
                if key in fields:
                    setattr(page, key, fields[key])
            page.validate()
            try:
                return await self.repo.create(page)
            except IntegrityError as exc:  # kolízia slug-u pri súbehu
                raise ConflictDomainError("Táto adresa stránky je už obsadená.") from exc

        existing.slug = slug
        for key in _EDITABLE_FIELDS:
            if key in fields:
                setattr(existing, key, fields[key])
        existing.updated_at = now
        existing.updated_by_user_id = actor_user_id
        existing.validate()
        try:
            return await self.repo.update(existing)
        except IntegrityError as exc:
            raise ConflictDomainError("Táto adresa stránky je už obsadená.") from exc

    async def publish(self, *, company_id, company_status: str, actor_user_id) -> CompanyPage:
        page = await self.repo.get_by_company_id(company_id)
        if page is None:
            raise NotFoundDomainError("Verejná stránka ešte nebola vytvorená.")

        status_value = str(getattr(company_status, "value", company_status) or "").lower()
        if status_value not in PUBLISHABLE_COMPANY_STATUSES:
            raise ValidationDomainError("Verejnú stránku môže zverejniť len overená firma.")

        missing = missing_publish_requirements(page)
        if missing:
            raise ValidationDomainError(
                "Na zverejnenie chýbajú povinné údaje: " + ", ".join(missing)
            )

        now = self.clock.now()
        page.status = CompanyPageStatus.PUBLISHED
        if page.published_at is None:
            page.published_at = now
        page.updated_at = now
        page.updated_by_user_id = actor_user_id
        return await self.repo.update(page)

    async def unpublish(self, *, company_id, actor_user_id) -> CompanyPage:
        page = await self.repo.get_by_company_id(company_id)
        if page is None:
            raise NotFoundDomainError("Verejná stránka ešte nebola vytvorená.")
        now = self.clock.now()
        page.status = CompanyPageStatus.DRAFT
        page.published_at = None
        page.updated_at = now
        page.updated_by_user_id = actor_user_id
        return await self.repo.update(page)


class CompanyPhotoService:
    def __init__(
        self,
        repo: CompanyPhotoRepository,
        page_repo: CompanyPageRepository,
        uuid_generator: UuidGenerator,
        clock: Clock,
    ):
        self.repo = repo
        self.page_repo = page_repo
        self.uuid_generator = uuid_generator
        self.clock = clock

    async def list(self, company_id) -> list[CompanyPhoto]:
        return await self.repo.list_by_company(company_id)

    async def add(
        self,
        *,
        company_id,
        file_url: str,
        caption: str | None,
        alt_text: str | None,
        actor_user_id,
    ) -> CompanyPhoto:
        count = await self.repo.count_by_company(company_id)
        if count >= MAX_PHOTOS:
            raise ValidationDomainError(f"Galéria je plná (maximum {MAX_PHOTOS} fotografií).")
        existing = await self.repo.list_by_company(company_id)
        is_first = len(existing) == 0
        now = self.clock.now()
        photo = CompanyPhoto(
            id=self.uuid_generator.new(),
            company_id=company_id,
            file_url=file_url,
            caption=caption,
            alt_text=alt_text,
            position=(max([p.position for p in existing], default=-1) + 1),
            is_primary=is_first,
            created_at=now,
            created_by_user_id=actor_user_id,
            updated_at=now,
            updated_by_user_id=actor_user_id,
        )
        photo.validate()
        return await self.repo.create(photo)

    async def _must_get(self, company_id, photo_id) -> CompanyPhoto:
        photo = await self.repo.get_by_id(photo_id)
        if photo is None or str(photo.company_id) != str(company_id):
            raise NotFoundDomainError("Fotografia neexistuje.")
        return photo

    async def update(
        self,
        *,
        company_id,
        photo_id,
        caption: str | None,
        alt_text: str | None,
        actor_user_id,
    ) -> CompanyPhoto:
        photo = await self._must_get(company_id, photo_id)
        if caption is not None:
            photo.caption = caption
        if alt_text is not None:
            photo.alt_text = alt_text
        photo.updated_at = self.clock.now()
        photo.updated_by_user_id = actor_user_id
        return await self.repo.update(photo)

    async def delete(self, *, company_id, photo_id) -> None:
        photo = await self._must_get(company_id, photo_id)
        await self.repo.delete(photo.id)
        if photo.is_primary:
            remaining = await self.repo.list_by_company(company_id)
            if remaining:
                new_primary = remaining[0]
                new_primary.is_primary = True
                new_primary.updated_at = self.clock.now()
                await self.repo.update(new_primary)

    async def reorder(self, *, company_id, ordered_ids: list, actor_user_id) -> list[CompanyPhoto]:
        photos = await self.repo.list_by_company(company_id)
        by_id = {str(p.id): p for p in photos}
        # Prijmeme len ID patriace tejto firme, v poradí podľa požiadavky;
        # zvyšné fotky doplníme na koniec v pôvodnom poradí.
        seen: set[str] = set()
        ordered: list[CompanyPhoto] = []
        for raw in ordered_ids:
            key = str(raw)
            if key in by_id and key not in seen:
                ordered.append(by_id[key])
                seen.add(key)
        for p in photos:
            if str(p.id) not in seen:
                ordered.append(p)
        now = self.clock.now()
        for index, p in enumerate(ordered):
            if p.position != index:
                p.position = index
                p.updated_at = now
                p.updated_by_user_id = actor_user_id
                await self.repo.update(p)
        return await self.repo.list_by_company(company_id)

    async def set_primary(self, *, company_id, photo_id, actor_user_id) -> list[CompanyPhoto]:
        photos = await self.repo.list_by_company(company_id)
        target = None
        for p in photos:
            if str(p.id) == str(photo_id):
                target = p
                break
        if target is None:
            raise NotFoundDomainError("Fotografia neexistuje.")
        now = self.clock.now()
        for p in photos:
            desired = str(p.id) == str(photo_id)
            if p.is_primary != desired:
                p.is_primary = desired
                p.updated_at = now
                p.updated_by_user_id = actor_user_id
                await self.repo.update(p)
        return await self.repo.list_by_company(company_id)
