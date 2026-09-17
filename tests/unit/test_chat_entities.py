"""Unit tests for chat entities."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.modules.chat.domain.entities import ChatMessageEntity, ChatThreadEntity
from app.modules.chat.domain.enums import ChatThreadStatus
from app.shared.domain.exceptions import ValidationDomainError


def _now():
    return datetime.now(UTC).replace(tzinfo=None)


def _thread(**over):
    base = {
        "id": uuid4(),
        "initiator_user_id": uuid4(),
        "initiator_company_id": None,
        "recipient_user_id": uuid4(),
        "recipient_company_id": None,
        "subject": "Test",
        "status": ChatThreadStatus.OPEN,
        "created_at": _now(),
        "updated_at": _now(),
    }
    base.update(over)
    return ChatThreadEntity(**base)


def test_thread_valid():
    t = _thread()
    t.validate()


def test_thread_empty_subject_raises():
    t = _thread(subject="")
    with pytest.raises(ValidationDomainError):
        t.validate()


def test_thread_self_chat_raises():
    uid = uuid4()
    t = _thread(initiator_user_id=uid, recipient_user_id=uid)
    with pytest.raises(ValidationDomainError):
        t.validate()


def test_message_valid():
    m = ChatMessageEntity(
        id=uuid4(),
        thread_id=uuid4(),
        sender_user_id=uuid4(),
        sender_company_id=None,
        body="Ahoj",
        created_at=_now(),
        updated_at=_now(),
    )
    m.validate()


def test_message_empty_raises():
    m = ChatMessageEntity(
        id=uuid4(),
        thread_id=uuid4(),
        sender_user_id=uuid4(),
        sender_company_id=None,
        body="   ",
        created_at=_now(),
        updated_at=_now(),
    )
    with pytest.raises(ValidationDomainError):
        m.validate()


def test_message_too_long_raises():
    m = ChatMessageEntity(
        id=uuid4(),
        thread_id=uuid4(),
        sender_user_id=uuid4(),
        sender_company_id=None,
        body="x" * 5001,
        created_at=_now(),
        updated_at=_now(),
    )
    with pytest.raises(ValidationDomainError):
        m.validate()
