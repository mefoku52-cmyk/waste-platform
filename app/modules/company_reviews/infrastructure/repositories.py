"""company_reviews repository implementation."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.company_reviews.domain.entities import CompanyReview
from app.modules.company_reviews.domain.repositories import CompanyReviewRepository
from app.modules.company_reviews.infrastructure.mappers import to_domain, to_model
from app.modules.company_reviews.infrastructure.models import CompanyReviewModel


def _as_str(value) -> str:
    return value if isinstance(value, str) else str(value)


class CompanyReviewRepositoryImpl(CompanyReviewRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, review_id) -> CompanyReview | None:
        model = await self.session.get(CompanyReviewModel, _as_str(review_id))
        return to_domain(model) if model else None

    async def get_by_company_author(self, company_id, author_user_id) -> CompanyReview | None:
        stmt = select(CompanyReviewModel).where(
            CompanyReviewModel.company_id == _as_str(company_id),
            CompanyReviewModel.author_user_id == _as_str(author_user_id),
        )
        model = (await self.session.execute(stmt)).scalar_one_or_none()
        return to_domain(model) if model else None

    async def list_by_company(
        self, company_id, *, statuses=None, page: int = 1, page_size: int = 20
    ) -> list[CompanyReview]:
        stmt = select(CompanyReviewModel).where(
            CompanyReviewModel.company_id == _as_str(company_id)
        )
        if statuses:
            values = [str(getattr(s, "value", s)) for s in statuses]
            stmt = stmt.where(CompanyReviewModel.status.in_(values))
        stmt = (
            stmt.order_by(CompanyReviewModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        models = (await self.session.execute(stmt)).scalars().all()
        return [to_domain(m) for m in models]

    async def count_by_company(self, company_id, *, statuses=None) -> int:
        stmt = (
            select(func.count())
            .select_from(CompanyReviewModel)
            .where(CompanyReviewModel.company_id == _as_str(company_id))
        )
        if statuses:
            values = [str(getattr(s, "value", s)) for s in statuses]
            stmt = stmt.where(CompanyReviewModel.status.in_(values))
        return int((await self.session.execute(stmt)).scalar_one())

    async def aggregate(self, company_id) -> dict:
        stmt = (
            select(func.avg(CompanyReviewModel.rating), func.count())
            .select_from(CompanyReviewModel)
            .where(CompanyReviewModel.company_id == _as_str(company_id))
            .where(CompanyReviewModel.status == "approved")
        )
        avg, count = (await self.session.execute(stmt)).one()
        return {
            "average": float(avg) if avg is not None else None,
            "count": int(count or 0),
        }

    async def create(self, review: CompanyReview) -> CompanyReview:
        model = to_model(review)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return to_domain(model)

    async def update(self, review: CompanyReview) -> CompanyReview:
        model = await self.session.get(CompanyReviewModel, str(review.id))
        if model is None:
            raise ValueError("Company review not found")
        model.rating = review.rating
        model.title = review.title
        model.body = review.body
        model.status = review.status.value
        model.moderated_by_user_id = (
            str(review.moderated_by_user_id) if review.moderated_by_user_id else None
        )
        model.moderated_at = review.moderated_at
        model.updated_at = review.updated_at
        model.updated_by_user_id = (
            str(review.updated_by_user_id) if review.updated_by_user_id else None
        )
        await self.session.commit()
        await self.session.refresh(model)
        return to_domain(model)
