"""compliance mappers."""

from ..domain.entities import ComplianceEntity
from .schemas import ComplianceResponse


def map_entity_to_response(entity: ComplianceEntity) -> ComplianceResponse:
    """Map entity to response."""
    return ComplianceResponse(
        id=str(entity.id),
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
