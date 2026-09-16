"""chat application services."""

import re
from datetime import datetime
from uuid import uuid4

from app.modules.chat.domain.entities import ChatMessageEntity, ChatThreadEntity
from app.modules.chat.domain.enums import ChatThreadStatus
from app.shared.domain.exceptions import NotFoundDomainError, ValidationDomainError

# Filter: skry telefon a email z textu spravy
PHONE_RE = re.compile(r"(\+?\d[\d\s\-\(\)]{7,}\d)")
EMAIL_RE = re.compile(r"[\w\.\-]+@[\w\.\-]+\.\w+")


def _sanitize(text: str) -> str:
    text = PHONE_RE.sub("[telefon skryty]", text)
    text = EMAIL_RE.sub("[email skryty]", text)
    return text


class ChatService:
    def __init__(self, repo):
        self.repo = repo

    async def create_thread(
        self,
        *,
        initiator_user_id,
        initiator_company_id,
        recipient_user_id,
        recipient_company_id,
        subject: str,
        listing_id=None,
    ) -> ChatThreadEntity:
        now = datetime.now()
        entity = ChatThreadEntity(
            id=uuid4(),
            listing_id=listing_id,
            initiator_user_id=initiator_user_id,
            initiator_company_id=initiator_company_id,
            recipient_user_id=recipient_user_id,
            recipient_company_id=recipient_company_id,
            subject=subject[:255],
            status=ChatThreadStatus.OPEN,
            last_message_at=now,
            created_at=now,
            updated_at=now,
            created_by_user_id=initiator_user_id,
            updated_by_user_id=initiator_user_id,
        )
        entity.validate()
        return await self.repo.create_thread(entity)

    async def get_thread(self, thread_id) -> ChatThreadEntity | None:
        return await self.repo.get_thread(thread_id)

    async def list_threads(self, user_id, page: int = 1, limit: int = 50):
        return await self.repo.list_threads_for_user(user_id, page, limit)

    async def count_threads(self, user_id) -> int:
        return await self.repo.count_threads_for_user(user_id)

    async def send_message(
        self,
        *,
        thread_id,
        sender_user_id,
        sender_company_id,
        body: str,
    ) -> ChatMessageEntity:
        thread = await self.repo.get_thread(thread_id)
        if thread is None:
            raise NotFoundDomainError("Thread not found")
        if sender_user_id not in (thread.initiator_user_id, thread.recipient_user_id):
            raise ValidationDomainError("Nie si ucastnik tejto konverzacie")

        sanitized = _sanitize(body)
        now = datetime.now()
        entity = ChatMessageEntity(
            id=uuid4(),
            thread_id=thread_id,
            sender_user_id=sender_user_id,
            sender_company_id=sender_company_id,
            body=sanitized,
            read_at=None,
            created_at=now,
            updated_at=now,
            created_by_user_id=sender_user_id,
            updated_by_user_id=sender_user_id,
        )
        entity.validate()
        return await self.repo.create_message(entity)

    async def list_messages(self, thread_id, page: int = 1, limit: int = 100):
        return await self.repo.list_messages(thread_id, page, limit)

    async def mark_read(self, thread_id, reader_user_id) -> int:
        return await self.repo.mark_messages_read(thread_id, reader_user_id)

    async def unread_count(self, user_id) -> int:
        return await self.repo.unread_count(user_id)
