"""inquiries mappers."""

from ..domain.entities import InquiriesEntity
from .schemas import InquiriesResponse


def map_entity_to_response(entity: InquiriesEntity) -> InquiriesResponse:
    """Map entity to response."""
    return InquiriesResponse(
        id=str(entity.id),
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
