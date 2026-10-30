"""AI conversation persistence – ABC + SQLAlchemy implementation."""

from __future__ import annotations

import json
import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_platform.domain.memory.ai_conversation import AiConversation
from app.modules.agent_platform.domain.memory.ai_message import AiMessage
from app.modules.agent_platform.domain.memory.ai_summary import AiSummary
from app.modules.agent_platform.infrastructure.models import (
    AiConversationModel,
    AiMessageModel,
)

# A rolling summary is stored as a message with this role inside the existing
# ai_messages table — no schema change, fully backward compatible.
SUMMARY_ROLE = "summary"


def _uuid_or_none(value: str | uuid.UUID | None) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        return None


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

    @abstractmethod
    async def count_messages(self, *, conversation_id: str) -> int:
        """Number of non-summary messages in the conversation."""
        ...

    @abstractmethod
    async def get_summary(self, *, conversation_id: str) -> AiSummary | None:
        """Return the latest rolling summary, or None."""
        ...

    @abstractmethod
    async def replace_summary(
        self,
        *,
        conversation_id: str,
        content: str,
        meta: dict[str, Any] | None = None,
    ) -> AiMessage | None:
        """Replace any existing summary with a newer one (atomic per call)."""
        ...


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
        uid = _uuid_or_none(user_id)
        cid = _uuid_or_none(company_id)

        stmt = select(AiConversationModel).where(AiConversationModel.session_id == session_id)
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            if existing.user_id != uid:
                raise PermissionError("conversation belongs to another user")
            if existing.company_id != cid:
                raise PermissionError("conversation belongs to another company")
            return _to_conv(existing)

        now = datetime.now(UTC).replace(tzinfo=None)
        model = AiConversationModel(
            id=uuid.uuid4(),
            session_id=session_id,
            user_id=uid,
            company_id=cid,
            created_at=now,
            updated_at=now,
        )
        self._session.add(model)
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            # race: re-load and re-check ownership
            existing = (await self._session.execute(stmt)).scalar_one_or_none()
            if existing is None:
                raise
            if existing.user_id != uid or existing.company_id != cid:
                raise PermissionError("conversation belongs to another actor")
            return _to_conv(existing)
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

    async def count_messages(self, *, conversation_id: str) -> int:
        cid = _uuid_or_none(conversation_id)
        if cid is None:
            return 0
        stmt = (
            select(func.count())
            .select_from(AiMessageModel)
            .where(
                AiMessageModel.conversation_id == cid,
                AiMessageModel.role != SUMMARY_ROLE,
            )
        )
        return int((await self._session.execute(stmt)).scalar() or 0)

    async def get_summary(self, *, conversation_id: str) -> AiSummary | None:
        cid = _uuid_or_none(conversation_id)
        if cid is None:
            return None
        stmt = (
            select(AiMessageModel)
            .where(
                AiMessageModel.conversation_id == cid,
                AiMessageModel.role == SUMMARY_ROLE,
            )
            .order_by(AiMessageModel.created_at.desc())
            .limit(1)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        meta: dict[str, Any] = {}
        if row.tool_calls:
            try:
                parsed = json.loads(row.tool_calls)
                if isinstance(parsed, dict):
                    meta = parsed
            except (TypeError, ValueError):
                meta = {}
        lang = meta.get("lang")
        return AiSummary(
            content=row.content or "",
            covers=int(meta.get("covers") or 0),
            language=str(lang) if lang else None,
            updated_at=(
                row.created_at.replace(tzinfo=UTC)
                if row.created_at and row.created_at.tzinfo is None
                else row.created_at
            ),
        )

    async def replace_summary(
        self,
        *,
        conversation_id: str,
        content: str,
        meta: dict[str, Any] | None = None,
    ) -> AiMessage | None:
        cid = _uuid_or_none(conversation_id)
        if cid is None:
            return None
        await self._session.execute(
            delete(AiMessageModel).where(
                AiMessageModel.conversation_id == cid,
                AiMessageModel.role == SUMMARY_ROLE,
            )
        )
        now = datetime.now(UTC).replace(tzinfo=None)
        model = AiMessageModel(
            id=uuid.uuid4(),
            conversation_id=cid,
            role=SUMMARY_ROLE,
            content=content,
            tool_calls=json.dumps(meta or {}, ensure_ascii=False),
            created_at=now,
        )
        self._session.add(model)
        conv = await self._session.get(AiConversationModel, cid)
        if conv is not None:
            conv.updated_at = now
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return _to_msg(model)
