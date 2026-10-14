"""company_reviews infrastructure mappers."""

from uuid import UUID

from app.modules.company_reviews.domain.entities import CompanyReview
from app.modules.company_reviews.domain.enums import ReviewStatus
from app.modules.company_reviews.infrastructure.models import CompanyReviewModel


def _uuid(value) -> UUID | None:
    if value is None:
        return None
    return value if isinstance(value, UUID) else UUID(str(value))


def to_domain(model: CompanyReviewModel) -> CompanyReview:
    return CompanyReview(
        id=_uuid(model.id),
        company_id=_uuid(model.company_id),
        author_user_id=_uuid(model.author_user_id),
        rating=model.rating,
        status=ReviewStatus(model.status),
        title=model.title,
        body=model.body,
        moderated_by_user_id=_uuid(model.moderated_by_user_id),
        moderated_at=model.moderated_at,
        created_at=model.created_at,
        created_by_user_id=_uuid(model.created_by_user_id),
        updated_at=model.updated_at,
        updated_by_user_id=_uuid(model.updated_by_user_id),
    )


def to_model(entity: CompanyReview) -> CompanyReviewModel:
    return CompanyReviewModel(
        id=str(entity.id),
        company_id=str(entity.company_id),
        author_user_id=str(entity.author_user_id),
        rating=entity.rating,
        status=entity.status.value,
        title=entity.title,
        body=entity.body,
        moderated_by_user_id=str(entity.moderated_by_user_id)
        if entity.moderated_by_user_id
        else None,
        moderated_at=entity.moderated_at,
        created_at=entity.created_at,
        created_by_user_id=str(entity.created_by_user_id) if entity.created_by_user_id else None,
        updated_at=entity.updated_at,
        updated_by_user_id=str(entity.updated_by_user_id) if entity.updated_by_user_id else None,
    )
