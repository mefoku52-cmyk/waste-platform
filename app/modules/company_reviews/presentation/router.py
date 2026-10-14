"""company_reviews private API router.

* ``POST /companies/{id}/reviews`` — odoslanie recenzie (oprávnený používateľ).
* ``GET  /companies/{id}/reviews`` — zoznam (člen/platform admin vidí všetky stavy).
* ``GET  /companies/{id}/reviews/mine`` — moja recenzia (na predvyplnenie).
* ``PATCH /companies/{id}/reviews/{review_id}/moderate`` — platform admin schváli/zamietne.
"""

from __future__ import annotations

import contextlib
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.presentation.dependencies import get_company_repo
from app.modules.company_reviews.application.services import CompanyReviewService
from app.modules.company_reviews.domain.enums import ReviewStatus
from app.modules.company_reviews.presentation.dependencies import (
    get_company_review_service,
)
from app.modules.company_reviews.presentation.mappers import to_review_data
from app.modules.company_reviews.presentation.schemas import (
    ReviewAggregate,
    ReviewAggregateResponse,
    ReviewModerateRequest,
    ReviewResponse,
    ReviewsResponse,
    ReviewSubmitRequest,
)
from app.shared.application.side_effects import write_audit
from app.shared.domain.exceptions import NotFoundDomainError
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import (
    current_user_id,
    is_company_member,
    is_platform_admin,
    require_platform_admin,
)
from app.shared.presentation.error_schemas import error_responses

router = APIRouter(prefix="/companies", tags=["company-reviews"])


async def _has_completed_inquiry(session: AsyncSession, company_id, user_id) -> bool:
    from app.modules.inquiries.infrastructure.models import InquiryModel

    try:
        company_uuid = uuid.UUID(str(company_id))
        author_uuid = uuid.UUID(str(user_id))
    except (ValueError, TypeError):
        return False
    stmt = (
        select(func.count())
        .select_from(InquiryModel)
        .where(InquiryModel.company_id == company_uuid)
        .where(InquiryModel.created_by_user_id == author_uuid)
        .where(InquiryModel.status.in_(("answered", "closed")))
    )
    return int((await session.execute(stmt)).scalar_one()) > 0


@router.post(
    "/{company_id}/reviews",
    response_model=ReviewResponse,
    status_code=201,
    responses=error_responses(401, 403, 404, 409, 422, 500),
)
async def submit_review(
    company_id: UUID,
    payload: ReviewSubmitRequest,
    current_user=Depends(require_current_user),
    company_repo=Depends(get_company_repo),
    service: CompanyReviewService = Depends(get_company_review_service),
    session: AsyncSession = Depends(get_db_session),
):
    company = await company_repo.get_by_id(company_id)
    if company is None:
        raise NotFoundDomainError("Firma neexistuje.")
    actor = current_user_id(current_user)
    is_member = is_company_member(current_user, company_id)
    has_inquiry = await _has_completed_inquiry(session, company_id, actor)
    review = await service.submit(
        company_id=company_id,
        author_user_id=actor,
        rating=payload.rating,
        title=payload.title,
        body=payload.body,
        is_member=is_member,
        has_completed_inquiry=has_inquiry,
    )
    with contextlib.suppress(Exception):
        await write_audit(
            session=session,
            actor_user_id=actor,
            action="company_review.submitted",
            target_type="company_review",
            target_id=review.id,
            details=f"companyId={company_id}; rating={review.rating}",
        )
    return ReviewResponse(data=to_review_data(review))


@router.get(
    "/{company_id}/reviews",
    response_model=ReviewsResponse,
    responses=error_responses(401, 403, 404, 500),
)
async def list_reviews(
    company_id: UUID,
    status: str | None = Query(default=None, pattern="^(pending|approved|rejected)$"),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    current_user=Depends(require_current_user),
    company_repo=Depends(get_company_repo),
    service: CompanyReviewService = Depends(get_company_review_service),
):
    company = await company_repo.get_by_id(company_id)
    if company is None:
        raise NotFoundDomainError("Firma neexistuje.")

    can_see_all = is_company_member(current_user, company_id) or is_platform_admin(current_user)
    if can_see_all:
        statuses = [ReviewStatus(status)] if status else None
    else:
        # Neverejný pohľad (neregistrovaný/nečlen) vidí len schválené.
        statuses = [ReviewStatus.APPROVED]

    items, total = await service.list_reviews(
        company_id=company_id, statuses=statuses, page=page, page_size=pageSize
    )
    return ReviewsResponse(
        items=[to_review_data(r) for r in items],
        meta={"page": page, "pageSize": pageSize, "total": total},
    )


@router.get(
    "/{company_id}/reviews/mine",
    response_model=ReviewAggregateResponse,
    responses=error_responses(401, 403, 500),
)
async def get_my_review(
    company_id: UUID,
    current_user=Depends(require_current_user),
    service: CompanyReviewService = Depends(get_company_review_service),
):
    # Autor recenzie je zámerne NIE člen firmy (viď pravidlá oprávnenosti),
    # preto tu nesmieme vyžadovať členstvo — vraciame výlučne vlastnú recenziu.
    actor = current_user_id(current_user)
    review = await service.get_mine(company_id=company_id, author_user_id=actor)
    if review is None:
        return ReviewAggregateResponse(
            data=ReviewAggregate(average=None, count=0, eligibility={"hasReview": False})
        )
    return ReviewAggregateResponse(
        data=ReviewAggregate(
            average=float(review.rating),
            count=1,
            eligibility={"hasReview": True},
        )
    )


@router.patch(
    "/{company_id}/reviews/{review_id}/moderate",
    response_model=ReviewResponse,
    responses=error_responses(401, 403, 404, 422, 500),
)
async def moderate_review(
    company_id: UUID,
    review_id: UUID,
    payload: ReviewModerateRequest,
    current_user=Depends(require_current_user),
    service: CompanyReviewService = Depends(get_company_review_service),
    session: AsyncSession = Depends(get_db_session),
):
    require_platform_admin(current_user)
    moderator = current_user_id(current_user)
    review = await service.moderate(
        review_id=review_id,
        status=ReviewStatus(payload.status),
        moderator_user_id=moderator,
    )
    with contextlib.suppress(Exception):
        await write_audit(
            session=session,
            actor_user_id=moderator,
            action="company_review.moderated",
            target_type="company_review",
            target_id=review.id,
            details=f"status={payload.status}",
        )
    return ReviewResponse(data=to_review_data(review))
