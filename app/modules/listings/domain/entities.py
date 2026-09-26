"""listings domain entities."""

from dataclasses import dataclass

from app.modules.listings.domain.enums import ListingsStatus
from app.shared.domain.base import AuditFields
from app.shared.domain.exceptions import ValidationDomainError


@dataclass(slots=True)
class ListingsEntity(AuditFields):
    """Listing entity - ponuka druhotneho materialu."""

    title: str
    material_type: str
    quantity: float
    unit: str
    condition: str
    location: str
    company_id: str
    status: ListingsStatus = ListingsStatus.DRAFT
    price: float | None = None
    currency: str = "EUR"
    description: str | None = None
    image_url: str | None = None
    promoted_until: str | None = None
    promoted_tier: str | None = None

    def validate(self) -> None:
        if not self.title:
            raise ValidationDomainError("Listing title is required")
        if not self.material_type:
            raise ValidationDomainError("Listing material_type is required")
        if self.quantity <= 0:
            raise ValidationDomainError("Listing quantity must be positive")
        if not self.company_id:
            raise ValidationDomainError("Listing company_id is required")
