"""listings mappers."""

from ..domain.entities import ListingsEntity
from .schemas import ListingData, ListingResponse


def map_entity_to_response(entity: ListingsEntity) -> ListingResponse:
    """Map entity to response."""
    return ListingResponse(
        data=ListingData(
            id=entity.id,
            title=entity.title,
            materialType=entity.material_type,
            quantity=entity.quantity,
            unit=entity.unit,
            price=entity.price,
            currency=entity.currency,
            condition=entity.condition,
            location=entity.location,
            status=entity.status.value,
            companyId=entity.company_id,
            description=entity.description,
            createdAt=entity.created_at,
            updatedAt=entity.updated_at,
        )
    )
