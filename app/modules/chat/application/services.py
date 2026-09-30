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


def _sanitize(text: str, *, allow_contacts: bool = False) -> str:
    """Skryje telefon a email z textu.

    Ak allow_contacts=True (firmy maju answered/closed inquiry medzi sebou),
    text sa necha nezmeneny.
    """
    if allow_contacts:
        return text
    text = PHONE_RE.sub("[telefon skryty]", text)
    text = EMAIL_RE.sub("[email skryty]", text)
    return text


class ChatService:
    def __init__(self, repo):
        self.repo = repo

    async def _has_revealed_relationship(self, thread) -> bool:
        """True ak medzi firmami v threade existuje inquiry answered/closed.

        Rovnaka logika ako v GET /companies/{id}/contacts.
        """
        a = str(thread.initiator_company_id) if thread.initiator_company_id else None
        b = str(thread.recipient_company_id) if thread.recipient_company_id else None
        if not a or not b or a == b:
            return False

        session = getattr(self.repo, "session", None)
        if session is None:
            return False

        try:
            from sqlalchemy import text

            r = await session.execute(
                text(
                    """
                    SELECT 1 FROM inquiries i
                    JOIN listings l ON l.id = i.listing_id
                    WHERE (
                        (i.company_id = :a AND l.company_id = :b)
                        OR (i.company_id = :b AND l.company_id = :a)
                    )
                    AND i.status IN ('answered', 'closed')
                    LIMIT 1
                    """
                ),
                {"a": a, "b": b},
            )
            return r.first() is not None
        except Exception:
            return False

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

    async def list_threads_detailed(self, user_id, page: int = 1, limit: int = 50):
        """Vrati thready s doplnenymi polami (lastMessage, unreadCount, counterpartUserId)."""
        threads = await self.repo.list_threads_for_user(user_id, page, limit)
        result = []
        for t in threads:
            # Counterpart = druha strana
            if str(t.initiator_user_id) == str(user_id):
                counterpart_id = t.recipient_user_id
            else:
                counterpart_id = t.initiator_user_id

            last_msg = await self.repo.get_last_message(t.id)
            unread = await self.repo.unread_count_in_thread(t.id, user_id)

            result.append(
                {
                    "thread": t,
                    "last_message": last_msg.body if last_msg else None,
                    "unread_count": unread,
                    "counterpart_user_id": counterpart_id,
                }
            )
        return result

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

        allow_contacts = await self._has_revealed_relationship(thread)
        sanitized = _sanitize(body, allow_contacts=allow_contacts)
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
