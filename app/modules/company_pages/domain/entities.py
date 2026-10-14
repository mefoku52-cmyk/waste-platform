"""company_pages domain entities."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.company_pages.application.slug import is_valid_slug
from app.modules.company_pages.domain.enums import CompanyPageStatus
from app.shared.domain.base import AuditFields
from app.shared.domain.exceptions import ValidationDomainError

# Polia, bez ktorých sa stránka nesmie publikovať. Kontakt stačí aspoň jeden.
REQUIRED_FOR_PUBLISH = ("display_name", "about_short")


@dataclass(slots=True)
class CompanyPage(AuditFields):
    """Verejná prezentácia firmy (projekcia firemných údajov).

    Kanonický zdroj firemných údajov ostáva ``companies``; táto entita
    uchováva len údaje špecifické pre verejnú stránku (o nás, verejné
    kontakty, slug, stav publikovania). Nikdy neduplikuje celý profil.
    """

    company_id: UUID
    slug: str
    status: CompanyPageStatus = CompanyPageStatus.DRAFT
    display_name: str | None = None
    tagline: str | None = None
    about_short: str | None = None
    about_long: str | None = None
    services: str | None = None
    specialization: str | None = None
    certifications: str | None = None
    opening_hours: str | None = None
    languages: str | None = None
    categories: str | None = None
    area: str | None = None
    public_email: str | None = None
    public_phone: str | None = None
    public_website: str | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    published_at: datetime | None = None

    def validate(self) -> None:
        if self.company_id is None:
            raise ValidationDomainError("Company page company_id is required")
        if not is_valid_slug(self.slug):
            raise ValidationDomainError("Invalid slug format")


@dataclass(slots=True)
class CompanyPhoto(AuditFields):
    """Fotografia vo verejnej galérii firmy."""

    company_id: UUID
    file_url: str
    caption: str | None = None
    alt_text: str | None = None
    position: int = 0
    is_primary: bool = False

    def validate(self) -> None:
        if self.company_id is None:
            raise ValidationDomainError("Company photo company_id is required")
        if not self.file_url:
            raise ValidationDomainError("Company photo file_url is required")


def missing_publish_requirements(page: CompanyPage) -> list[str]:
    """Zoznam chýbajúcich polí, ktoré blokujú publikovanie.

    Slúži na zrozumiteľnú spätnú väzbu v editore (stav dokončenia).
    """
    missing: list[str] = []
    if not (page.display_name or "").strip():
        missing.append("displayName")
    if not (page.about_short or "").strip():
        missing.append("aboutShort")
    if not ((page.public_email or "").strip() or (page.public_phone or "").strip()):
        missing.append("contact")
    return missing
