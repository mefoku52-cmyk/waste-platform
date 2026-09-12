"""inquiries mappers."""

from ..domain.entities import InquiryEntity
from .schemas import InquiryResponse


def map_entity_to_response(entity: InquiryEntity) -> InquiryResponse:
    """Map entity to response."""
    return InquiryResponse(
        data=entity,
        id=str(entity.id),
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
