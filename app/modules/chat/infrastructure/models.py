"""chat database models."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.shared.infrastructure.db.base import Base


class ChatThreadModel(Base):
    __tablename__ = "chat_threads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), nullable=True)
    initiator_user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    initiator_company_id = Column(UUID(as_uuid=True), nullable=True)
    recipient_user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    recipient_company_id = Column(UUID(as_uuid=True), nullable=True)
    subject = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False, default="open", server_default="open")
    last_message_at = Column(DateTime, nullable=True, default=lambda: datetime.now())
    created_at = Column(DateTime, default=lambda: datetime.now())
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(),
        onupdate=lambda: datetime.now(),
    )
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    updated_by_user_id = Column(UUID(as_uuid=True), nullable=True)


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_user_id = Column(UUID(as_uuid=True), nullable=False)
    sender_company_id = Column(UUID(as_uuid=True), nullable=True)
    body = Column(Text, nullable=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(), index=True)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(),
        onupdate=lambda: datetime.now(),
    )
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    updated_by_user_id = Column(UUID(as_uuid=True), nullable=True)
