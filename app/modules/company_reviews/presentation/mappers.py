"""company_reviews presentation mappers."""

from app.modules.company_reviews.domain.entities import CompanyReview
from app.modules.company_reviews.presentation.schemas import ReviewData


def to_review_data(review: CompanyReview) -> ReviewData:
    return ReviewData(
        id=str(review.id),
        companyId=str(review.company_id),
        authorUserId=str(review.author_user_id) if review.author_user_id else None,
        rating=review.rating,
        title=review.title,
        body=review.body,
        status=str(getattr(review.status, "value", review.status)),
        moderatedAt=review.moderated_at,
        createdAt=review.created_at,
        updatedAt=review.updated_at,
    )
