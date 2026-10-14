"""company_reviews application service.

Pravidlá oprávnenosti (serverové, nie len klientske):
* Recenzovať môže len prihlásený používateľ, ktorý NIE JE členom firmy.
* A musí mať s firmou ukončenú interakciu — existujúci dopyt (inquiry) so
  stavom ``answered`` alebo ``closed``, ktorý sám vytvoril. Tým sa zabráni
  falošným recenziám od náhodných účtov.
* Nová recenzia má stav ``pending`` (moderácia). Duplicity rieši UNIQUE
  obmedzenie (jedna recenzia na používateľa a firmu).
"""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from app.modules.company_reviews.domain.entities import CompanyReview
from app.modules.company_reviews.domain.enums import ReviewStatus
from app.modules.company_reviews.domain.repositories import CompanyReviewRepository
from app.shared.application.clock import Clock
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.domain.exceptions import (
    ConflictDomainError,
    ForbiddenDomainError,
    NotFoundDomainError,
    ValidationDomainError,
)


class CompanyReviewService:
    def __init__(
        self,
        repo: CompanyReviewRepository,
        uuid_generator: UuidGenerator,
        clock: Clock,
    ):
        self.repo = repo
        self.uuid_generator = uuid_generator
        self.clock = clock

    async def submit(
        self,
        *,
        company_id,
        author_user_id,
        rating: int,
        title: str | None,
        body: str | None,
        is_member: bool,
        has_completed_inquiry: bool,
    ) -> CompanyReview:
        if is_member:
            raise ForbiddenDomainError("Člen firmy nemôže recenzovať vlastnú firmu.")
        if not has_completed_inquiry:
            raise ForbiddenDomainError(
                "Recenzovať môžete až po ukončenej komunikácii s firmou (dopyte)."
            )
        existing = await self.repo.get_by_company_author(company_id, author_user_id)
        if existing is not None:
            raise ConflictDomainError("Pre túto firmu ste už recenziu odoslali.")

        now = self.clock.now()
        review = CompanyReview(
            id=self.uuid_generator.new(),
            company_id=company_id,
            author_user_id=author_user_id,
            rating=int(rating),
            title=(title or None),
            body=(body or None),
            status=ReviewStatus.PENDING,
            created_at=now,
            created_by_user_id=author_user_id,
            updated_at=now,
            updated_by_user_id=author_user_id,
        )
        review.validate()
        try:
            return await self.repo.create(review)
        except IntegrityError as exc:
            raise ConflictDomainError("Pre túto firmu ste už recenziu odoslali.") from exc

    async def get_mine(self, *, company_id, author_user_id) -> CompanyReview | None:
        return await self.repo.get_by_company_author(company_id, author_user_id)

    async def list_reviews(
        self,
        *,
        company_id,
        statuses=None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[CompanyReview], int]:
        items = await self.repo.list_by_company(
            company_id, statuses=statuses, page=page, page_size=page_size
        )
        total = await self.repo.count_by_company(company_id, statuses=statuses)
        return items, total

    async def moderate(
        self, *, review_id, status: ReviewStatus, moderator_user_id
    ) -> CompanyReview:
        review = await self.repo.get_by_id(review_id)
        if review is None:
            raise NotFoundDomainError("Recenzia neexistuje.")
        if status not in (ReviewStatus.APPROVED, ReviewStatus.REJECTED):
            raise ValidationDomainError("Neplatný stav moderácie.")
        now = self.clock.now()
        review.status = status
        review.moderated_by_user_id = moderator_user_id
        review.moderated_at = now
        review.updated_at = now
        review.updated_by_user_id = moderator_user_id
        return await self.repo.update(review)

    async def public_summary(self, company_id) -> dict:
        """Schválené recenzie + agregátne hodnotenie pre verejnú stránku."""
        items = await self.repo.list_by_company(
            company_id, statuses=[ReviewStatus.APPROVED], page=1, page_size=50
        )
        agg = await self.repo.aggregate(company_id)
        return {"items": items, "average": agg["average"], "count": agg["count"]}
