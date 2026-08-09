"""admin mappers."""

from ..domain.entities import AdminAuditEntryEntity
from .schemas import AdminAuditEntryResponse


def map_entity_to_response(entity: AdminAuditEntryEntity) -> AdminAuditEntryResponse:
    """Map entity to response."""
    return AdminAuditEntryResponse(
        id=str(entity.id),
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
