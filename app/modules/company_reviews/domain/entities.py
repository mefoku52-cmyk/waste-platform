"""company_reviews domain entity."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.company_reviews.domain.enums import ReviewStatus
from app.shared.domain.base import AuditFields
from app.shared.domain.exceptions import ValidationDomainError

MIN_RATING = 1
MAX_RATING = 5
MAX_TITLE_LENGTH = 120
MAX_BODY_LENGTH = 2000


@dataclass(slots=True)
class CompanyReview(AuditFields):
    company_id: UUID
    author_user_id: UUID
    rating: int
    status: ReviewStatus = ReviewStatus.PENDING
    title: str | None = None
    body: str | None = None
    moderated_by_user_id: UUID | None = None
    moderated_at: datetime | None = None

    def validate(self) -> None:
        if self.company_id is None:
            raise ValidationDomainError("Review company_id is required")
        if self.author_user_id is None:
            raise ValidationDomainError("Review author_user_id is required")
        if not isinstance(self.rating, int) or not (MIN_RATING <= self.rating <= MAX_RATING):
            raise ValidationDomainError(
                f"Hodnotenie musí byť celé číslo {MIN_RATING}-{MAX_RATING}."
            )
        if self.title is not None and len(self.title) > MAX_TITLE_LENGTH:
            raise ValidationDomainError(
                f"Nadpis recenzie môže mať najviac {MAX_TITLE_LENGTH} znakov."
            )
        if self.body is not None and len(self.body) > MAX_BODY_LENGTH:
            raise ValidationDomainError(f"Text recenzie môže mať najviac {MAX_BODY_LENGTH} znakov.")
