"""listings infrastructure mappers - domain entity <-> SQLAlchemy model."""

import uuid

from app.modules.listings.domain.entities import ListingsEntity


def _uuid(value):
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
from app.modules.listings.domain.enums import ListingsStatus
from app.modules.listings.infrastructure.models import ListingsModel


def to_domain(model: ListingsModel) -> ListingsEntity:
    promoted_until = getattr(model, "promoted_until", None)
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
        promoted_until=promoted_until.isoformat() if promoted_until else None,
        promoted_tier=getattr(model, "promoted_tier", None),
    )


def to_model(entity: ListingsEntity) -> ListingsModel:
    model = ListingsModel(
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
        company_id=_uuid(entity.company_id),
        description=entity.description,
        image_url=getattr(entity, "image_url", None),
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        created_by_user_id=entity.created_by_user_id,
        updated_by_user_id=entity.updated_by_user_id,
    )
    if getattr(entity, "promoted_until", None):
        from datetime import datetime

        try:
            model.promoted_until = datetime.fromisoformat(entity.promoted_until)
        except (TypeError, ValueError):
            model.promoted_until = None
    if getattr(entity, "promoted_tier", None):
        model.promoted_tier = entity.promoted_tier
    return model
