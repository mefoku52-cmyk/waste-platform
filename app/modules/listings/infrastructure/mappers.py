"""listings infrastructure mappers - domain entity <-> SQLAlchemy model."""

from app.modules.listings.domain.entities import ListingsEntity
from app.modules.listings.domain.enums import ListingsStatus
from app.modules.listings.infrastructure.models import ListingsModel


def to_domain(model: ListingsModel) -> ListingsEntity:
    return ListingsEntity(
        id=model.id,
        title=model.title,
        material_type=model.material_type,
        quantity=model.quantity,
        unit=model.unit,
        price=model.price,
        currency=model.currency,
        condition=model.condition,
        location=model.location,
        status=ListingsStatus(model.status),
        company_id=str(model.company_id) if model.company_id else None,
        description=model.description,
        image_url=getattr(model, "image_url", None),
        created_at=model.created_at,
        updated_at=model.updated_at,
        created_by_user_id=model.created_by_user_id,
        updated_by_user_id=model.updated_by_user_id,
    )


def to_model(entity: ListingsEntity) -> ListingsModel:
    return ListingsModel(
        id=entity.id,
        title=entity.title,
        material_type=entity.material_type,
        quantity=entity.quantity,
        unit=entity.unit,
        price=entity.price,
        currency=entity.currency,
        condition=entity.condition,
        location=entity.location,
        status=entity.status.value,
        company_id=entity.company_id,
        description=entity.description,
        image_url=getattr(entity, "image_url", None),
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        created_by_user_id=entity.created_by_user_id,
        updated_by_user_id=entity.updated_by_user_id,
    )
