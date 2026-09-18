"""Round-trip tests for the notifications persistence mappers.

These were previously at 0% coverage. The mappers are the seam between the
domain entity (snake_case, UUID/datetime objects) and the SQLAlchemy model, so a
field dropped here silently loses data on write.
"""

from datetime import datetime
from uuid import uuid4

import pytest

from app.modules.notifications.domain.entities import NotificationEntity
from app.modules.notifications.infrastructure.mappers import to_domain, to_model
from app.modules.notifications.infrastructure.models import NotificationModel


def _entity(**over):
    base = {
        "id": uuid4(),
        "user_id": uuid4(),
        "type": "inquiry_received",
        "title": "Novy dopyt",
        "message": "Mate novy dopyt",
        "is_read": False,
        "related_entity_id": uuid4(),
        "created_at": datetime(2026, 9, 17, 10, 30, 0),
        "updated_at": datetime(2026, 9, 17, 10, 31, 0),
        "created_by_user_id": None,
        "updated_by_user_id": None,
    }
    base.update(over)
    return NotificationEntity(**base)


def test_to_model_copies_every_field():
    entity = _entity()

    model = to_model(entity)

    assert isinstance(model, NotificationModel)
    assert model.id == entity.id
    assert model.user_id == entity.user_id
    assert model.type == entity.type
    assert model.title == entity.title
    assert model.message == entity.message
    assert model.is_read is False
    assert model.related_entity_id == entity.related_entity_id
    assert model.created_at == entity.created_at
    assert model.updated_at == entity.updated_at


def test_to_domain_copies_every_field():
    entity = _entity(is_read=True)

    restored = to_domain(to_model(entity))

    assert isinstance(restored, NotificationEntity)
    assert restored.id == entity.id
    assert restored.user_id == entity.user_id
    assert restored.type == entity.type
    assert restored.title == entity.title
    assert restored.message == entity.message
    assert restored.is_read is True
    assert restored.related_entity_id == entity.related_entity_id
    assert restored.created_at == entity.created_at
    assert restored.updated_at == entity.updated_at


def test_entity_model_round_trip_is_lossless():
    entity = _entity(is_read=True)

    assert to_domain(to_model(entity)) == entity


@pytest.mark.parametrize("related", [None, uuid4()])
def test_optional_related_entity_id_survives_round_trip(related):
    entity = _entity(related_entity_id=related)

    assert to_domain(to_model(entity)).related_entity_id == related


def test_audit_attribution_survives_round_trip():
    actor = uuid4()
    entity = _entity(created_by_user_id=actor, updated_by_user_id=actor)

    restored = to_domain(to_model(entity))

    assert restored.created_by_user_id == actor
    assert restored.updated_by_user_id == actor
