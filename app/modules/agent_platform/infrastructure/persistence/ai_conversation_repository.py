"""AI conversation persistence – ABC + SQLAlchemy implementation."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_platform.domain.memory.ai_conversation import AiConversation
from app.modules.agent_platform.domain.memory.ai_message import AiMessage
from app.modules.agent_platform.infrastructure.models import (
    AiConversationModel,
    AiMessageModel,
)


def _to_conv(model: AiConversationModel) -> AiConversation:
    return AiConversation(
        id=str(model.id),
        session_id=model.session_id,
        user_id=str(model.user_id),
        company_id=str(model.company_id) if model.company_id else None,
        created_at=model.created_at.replace(tzinfo=UTC)
        if model.created_at.tzinfo is None
        else model.created_at,
        updated_at=model.updated_at.replace(tzinfo=UTC)
        if model.updated_at.tzinfo is None
        else model.updated_at,
    )


def _to_msg(model: AiMessageModel) -> AiMessage:
    return AiMessage(
        id=str(model.id),
        conversation_id=str(model.conversation_id),
        role=model.role,
        content=model.content or "",
        tool_calls=model.tool_calls,
        created_at=model.created_at.replace(tzinfo=UTC)
        if model.created_at.tzinfo is None
        else model.created_at,
    )


class AiConversationRepository(ABC):
    @abstractmethod
    async def get_or_create(
        self,
        *,
        session_id: str,
        user_id: str,
        company_id: str | None,
    ) -> AiConversation: ...

    @abstractmethod
    async def get_messages(
        self,
        *,
        conversation_id: str,
        limit: int = 20,
    ) -> list[AiMessage]: ...

    @abstractmethod
    async def append_message(
        self,
        *,
        conversation_id: str,
        role: str,
        content: str,
        tool_calls: str | None = None,
    ) -> AiMessage: ...


class SqlAlchemyAiConversationRepository(AiConversationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(
        self,
        *,
        session_id: str,
        user_id: str,
        company_id: str | None,
    ) -> AiConversation:
        stmt = select(AiConversationModel).where(AiConversationModel.session_id == session_id)
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            return _to_conv(existing)

        now = datetime.now(UTC).replace(tzinfo=None)
        model = AiConversationModel(
            id=uuid.uuid4(),
            session_id=session_id,
            user_id=user_id,
            company_id=company_id,
            created_at=now,
            updated_at=now,
        )
        self._session.add(model)
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return _to_conv(model)

    async def get_messages(
        self,
        *,
        conversation_id: str,
        limit: int = 20,
    ) -> list[AiMessage]:
        try:
            cid = uuid.UUID(conversation_id)
        except (ValueError, TypeError):
            return []

        # Najnovsich N, potom reverse na chronologicke poradie
        stmt = (
            select(AiMessageModel)
            .where(AiMessageModel.conversation_id == cid)
            .order_by(AiMessageModel.created_at.desc())
            .limit(limit)
        )
        rows = list((await self._session.execute(stmt)).scalars().all())
        rows.reverse()
        return [_to_msg(r) for r in rows]

    async def append_message(
        self,
        *,
        conversation_id: str,
        role: str,
        content: str,
        tool_calls: str | None = None,
    ) -> AiMessage:
        try:
            cid = uuid.UUID(conversation_id)
        except (ValueError, TypeError):
            raise ValueError("Invalid conversation id")

        now = datetime.now(UTC).replace(tzinfo=None)
        msg = AiMessageModel(
            id=uuid.uuid4(),
            conversation_id=cid,
            role=role,
            content=content,
            tool_calls=tool_calls,
            created_at=now,
        )
        self._session.add(msg)

        conv = await self._session.get(AiConversationModel, cid)
        if conv is not None:
            conv.updated_at = now

        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return _to_msg(msg)
