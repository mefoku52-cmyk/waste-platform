"""chat repository implementation."""

import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.chat.domain.entities import ChatMessageEntity, ChatThreadEntity
from app.modules.chat.domain.repositories import ChatRepository
from app.modules.chat.infrastructure.mappers import (
    message_to_domain,
    message_to_model,
    thread_to_domain,
    thread_to_model,
)
from app.modules.chat.infrastructure.models import ChatMessageModel, ChatThreadModel


def _uid(x):
    if x is None:
        return None
    return x if isinstance(x, uuid.UUID) else uuid.UUID(str(x))


class ChatRepositoryImpl(ChatRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_thread(self, entity: ChatThreadEntity) -> ChatThreadEntity:
        m = thread_to_model(entity)
        self.session.add(m)
        await self.session.commit()
        await self.session.refresh(m)
        return thread_to_domain(m)

    async def get_thread(self, thread_id) -> ChatThreadEntity | None:
        r = await self.session.execute(
            select(ChatThreadModel).where(ChatThreadModel.id == _uid(thread_id))
        )
        m = r.scalar_one_or_none()
        return thread_to_domain(m) if m else None

    async def list_threads_for_user(self, user_id, page: int = 1, limit: int = 50):
        u = _uid(user_id)
        offset = (page - 1) * limit
        r = await self.session.execute(
            select(ChatThreadModel)
            .where(
                (ChatThreadModel.initiator_user_id == u) | (ChatThreadModel.recipient_user_id == u)
            )
            .order_by(ChatThreadModel.last_message_at.desc().nullslast())
            .offset(offset)
            .limit(limit)
        )
        return [thread_to_domain(m) for m in r.scalars().all()]

    async def count_threads_for_user(self, user_id) -> int:
        u = _uid(user_id)
        r = await self.session.execute(
            select(func.count())
            .select_from(ChatThreadModel)
            .where(
                (ChatThreadModel.initiator_user_id == u) | (ChatThreadModel.recipient_user_id == u)
            )
        )
        return int(r.scalar_one())

    async def update_thread(self, entity: ChatThreadEntity) -> ChatThreadEntity:
        m = await self.session.get(ChatThreadModel, _uid(entity.id))
        if m is None:
            raise ValueError("Thread not found")
        m.subject = entity.subject
        m.status = entity.status.value
        m.last_message_at = entity.last_message_at
        m.updated_at = entity.updated_at
        await self.session.commit()
        await self.session.refresh(m)
        return thread_to_domain(m)

    async def create_message(self, entity: ChatMessageEntity) -> ChatMessageEntity:
        m = message_to_model(entity)
        self.session.add(m)
        await self.session.commit()
        await self.session.refresh(m)
        # Update thread last_message_at
        await self.session.execute(
            update(ChatThreadModel)
            .where(ChatThreadModel.id == _uid(entity.thread_id))
            .values(last_message_at=entity.created_at, updated_at=datetime.now())
        )
        await self.session.commit()
        return message_to_domain(m)

    async def list_messages(self, thread_id, page: int = 1, limit: int = 100):
        offset = (page - 1) * limit
        r = await self.session.execute(
            select(ChatMessageModel)
            .where(ChatMessageModel.thread_id == _uid(thread_id))
            .order_by(ChatMessageModel.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return [message_to_domain(m) for m in r.scalars().all()]

    async def count_messages(self, thread_id) -> int:
        r = await self.session.execute(
            select(func.count())
            .select_from(ChatMessageModel)
            .where(ChatMessageModel.thread_id == _uid(thread_id))
        )
        return int(r.scalar_one())

    async def mark_messages_read(self, thread_id, reader_user_id) -> int:
        u = _uid(reader_user_id)
        # Najprv spocitaj kolko treba oznacit
        count_stmt = (
            select(func.count())
            .select_from(ChatMessageModel)
            .where(ChatMessageModel.thread_id == _uid(thread_id))
            .where(ChatMessageModel.sender_user_id != u)
            .where(ChatMessageModel.read_at.is_(None))
        )
        count_result = await self.session.execute(count_stmt)
        count = int(count_result.scalar_one())

        if count > 0:
            await self.session.execute(
                update(ChatMessageModel)
                .where(ChatMessageModel.thread_id == _uid(thread_id))
                .where(ChatMessageModel.sender_user_id != u)
                .where(ChatMessageModel.read_at.is_(None))
                .values(read_at=datetime.now())
            )
            await self.session.commit()
        return count

    async def unread_count(self, user_id) -> int:
        u = _uid(user_id)
        r = await self.session.execute(
            select(func.count())
            .select_from(ChatMessageModel)
            .join(ChatThreadModel, ChatMessageModel.thread_id == ChatThreadModel.id)
            .where(
                (ChatThreadModel.initiator_user_id == u) | (ChatThreadModel.recipient_user_id == u)
            )
            .where(ChatMessageModel.sender_user_id != u)
            .where(ChatMessageModel.read_at.is_(None))
        )
        return int(r.scalar_one())
