"""Unit tests for ChatService."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.chat.application.services import ChatService
from app.modules.chat.domain.entities import ChatThreadEntity
from app.modules.chat.domain.enums import ChatThreadStatus
from app.shared.domain.exceptions import NotFoundDomainError, ValidationDomainError


def _thread(**over):
    base = {
        "id": uuid4(),
        "initiator_user_id": uuid4(),
        "initiator_company_id": None,
        "recipient_user_id": uuid4(),
        "recipient_company_id": None,
        "subject": "Test",
        "status": ChatThreadStatus.OPEN,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    base.update(over)
    return ChatThreadEntity(**base)


@pytest.mark.asyncio
async def test_create_thread_validates_self_chat():
    repo = MagicMock()
    svc = ChatService(repo)
    uid = uuid4()
    with pytest.raises(ValidationDomainError):
        await svc.create_thread(
            initiator_user_id=uid,
            initiator_company_id=None,
            recipient_user_id=uid,
            recipient_company_id=None,
            subject="self",
        )


@pytest.mark.asyncio
async def test_create_thread_success():
    t = _thread()
    repo = MagicMock()
    repo.create_thread = AsyncMock(return_value=t)
    svc = ChatService(repo)
    result = await svc.create_thread(
        initiator_user_id=t.initiator_user_id,
        initiator_company_id=None,
        recipient_user_id=t.recipient_user_id,
        recipient_company_id=None,
        subject="ahoj",
    )
    assert result is t
    repo.create_thread.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_message_thread_not_found():
    repo = MagicMock()
    repo.get_thread = AsyncMock(return_value=None)
    svc = ChatService(repo)
    with pytest.raises(NotFoundDomainError):
        await svc.send_message(
            thread_id=str(uuid4()),
            sender_user_id=uuid4(),
            sender_company_id=None,
            body="ahoj",
        )


@pytest.mark.asyncio
async def test_send_message_not_participant():
    t = _thread()
    stranger = uuid4()
    repo = MagicMock()
    repo.get_thread = AsyncMock(return_value=t)
    svc = ChatService(repo)
    with pytest.raises(ValidationDomainError):
        await svc.send_message(
            thread_id=str(t.id),
            sender_user_id=stranger,
            sender_company_id=None,
            body="ahoj",
        )


@pytest.mark.asyncio
async def test_send_message_sanitizes_body():
    t = _thread()
    repo = MagicMock()
    repo.get_thread = AsyncMock(return_value=t)
    captured = {}

    async def _fake_create(entity):
        captured["body"] = entity.body
        return entity

    repo.create_message = AsyncMock(side_effect=_fake_create)
    svc = ChatService(repo)
    await svc.send_message(
        thread_id=str(t.id),
        sender_user_id=t.initiator_user_id,
        sender_company_id=None,
        body="mail x@y.sk tel 0900123456",
    )
    assert "x@y.sk" not in captured["body"]
    assert "0900123456" not in captured["body"]
    assert "[email skryty]" in captured["body"]
    assert "[telefon skryty]" in captured["body"]


@pytest.mark.asyncio
async def test_mark_read_delegates():
    repo = MagicMock()
    repo.mark_messages_read = AsyncMock(return_value=3)
    svc = ChatService(repo)
    n = await svc.mark_read(str(uuid4()), uuid4())
    assert n == 3


@pytest.mark.asyncio
async def test_unread_count_delegates():
    repo = MagicMock()
    repo.unread_count = AsyncMock(return_value=2)
    svc = ChatService(repo)
    assert await svc.unread_count(uuid4()) == 2
