"""Agent Platform database models."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.shared.infrastructure.db.base import Base


class AiConversationModel(Base):
    __tablename__ = "ai_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(64), nullable=False, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(),
        onupdate=lambda: datetime.now(),
    )


class AiMessageModel(Base):
    __tablename__ = "ai_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(16), nullable=False)  # user | assistant | tool
    content = Column(Text, nullable=False)
    tool_calls = Column(Text, nullable=True)  # JSON string, optional
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(), index=True)

    __table_args__ = (Index("ix_ai_messages_conv_created", "conversation_id", "created_at"),)
