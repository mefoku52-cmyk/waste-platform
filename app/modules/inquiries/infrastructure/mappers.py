"""inquiries infrastructure mappers."""

from app.modules.inquiries.domain.entities import InquiryEntity
from app.modules.inquiries.domain.enums import InquiryStatus
from app.modules.inquiries.infrastructure.models import InquiryModel


def to_domain(model: InquiryModel) -> InquiryEntity:
    return InquiryEntity(
        id=model.id,
        listing_id=model.listing_id,
        company_id=model.company_id,
        message=model.message,
        contact_email=model.contact_email,
        contact_phone=model.contact_phone,
        status=InquiryStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
        created_by_user_id=model.created_by_user_id,
        updated_by_user_id=model.updated_by_user_id,
    )


def to_model(entity: InquiryEntity) -> InquiryModel:
    return InquiryModel(
        id=entity.id,
        listing_id=entity.listing_id,
        company_id=entity.company_id,
        message=entity.message,
        contact_email=entity.contact_email,
        contact_phone=entity.contact_phone,
        status=entity.status.value,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        created_by_user_id=entity.created_by_user_id,
        updated_by_user_id=entity.updated_by_user_id,
    )
