"""Tests for the notifications API schemas and presentation mapper.

The router builds ``NotificationData`` through a local ``_to_data`` helper; the
``map_entity_to_response`` function in the mappers module is unreferenced.
"""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.notifications.domain.entities import NotificationEntity
from app.modules.notifications.presentation.mappers import map_entity_to_response
from app.modules.notifications.presentation.schemas import (
    NotificationCreateRequest,
    NotificationData,
    NotificationResponse,
    PaginatedNotificationsResponse,
    PaginationMeta,
)


def _entity(**over):
    base = {
        "user_id": uuid4(),
        "type": "inquiry_received",
        "title": "Novy dopyt",
        "message": "Mate novy dopyt",
        "is_read": False,
    }
    base.update(over)
    return NotificationEntity(**base)


# --------------------------------------------------------------------------
# create request validation
# --------------------------------------------------------------------------


def test_create_request_accepts_valid_payload():
    uid = uuid4()

    request = NotificationCreateRequest(userId=uid, type="inquiry_received", title="T", message="M")

    assert request.userId == uid
    assert request.isRead is False
    assert request.relatedEntityId is None


def test_create_request_requires_type():
    with pytest.raises(ValidationError):
        NotificationCreateRequest(userId=uuid4(), type="", title="T", message="M")


def test_create_request_requires_title():
    with pytest.raises(ValidationError):
        NotificationCreateRequest(userId=uuid4(), type="t", title="", message="M")


def test_create_request_requires_message():
    with pytest.raises(ValidationError):
        NotificationCreateRequest(userId=uuid4(), type="t", title="T", message="")


def test_create_request_rejects_overlong_message():
    """message is capped at 2000 chars; the side-effect helper relies on this."""
    with pytest.raises(ValidationError):
        NotificationCreateRequest(userId=uuid4(), type="t", title="T", message="x" * 2001)


def test_create_request_accepts_message_at_the_cap():
    request = NotificationCreateRequest(userId=uuid4(), type="t", title="T", message="x" * 2000)

    assert len(request.message) == 2000


def test_create_request_rejects_invalid_uuid():
    with pytest.raises(ValidationError):
        NotificationCreateRequest(userId="not-a-uuid", type="t", title="T", message="M")


# --------------------------------------------------------------------------
# response models
# --------------------------------------------------------------------------


def test_response_serialises_snake_case_entity_into_camel_case_json():
    """The local router helper is the supported mapping path."""
    from app.modules.notifications.presentation.router import _to_data

    entity = _entity()
    payload = NotificationResponse(data=_to_data(entity)).model_dump(mode="json")

    assert payload["data"]["userId"] == str(entity.user_id)
    assert payload["data"]["isRead"] is False
    assert payload["data"]["title"] == entity.title


def test_data_model_rejects_invalid_field_type():
    with pytest.raises(ValidationError):
        NotificationData(
            id="not-a-uuid",
            userId=uuid4(),
            type="t",
            title="T",
            message="M",
            isRead=False,
            relatedEntityId=None,
            createdAt=datetime.now(),
            updatedAt=datetime.now(),
        )


def test_map_entity_to_response_builds_a_data_model():
    entity = _entity()

    response = map_entity_to_response(entity)

    assert response.data.userId == entity.user_id


def test_paginated_response_shape():
    meta = PaginationMeta(page=1, pageSize=10, total=0)

    payload = PaginatedNotificationsResponse(items=[], meta=meta).model_dump(mode="json")

    assert payload["items"] == []
    assert payload["meta"] == {"page": 1, "pageSize": 10, "total": 0}
