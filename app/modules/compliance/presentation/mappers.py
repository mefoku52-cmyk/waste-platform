"""compliance mappers."""

from ..domain.entities import ComplianceRecordEntity
from .schemas import ComplianceRecordResponse


def map_entity_to_response(entity: ComplianceRecordEntity) -> ComplianceRecordResponse:
    """Map entity to response."""
    return ComplianceRecordResponse(
        id=str(entity.id),
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
