"""Agent Platform database models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, String, Text
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


# ─────────────────────────────────────────────────────────────
# GOVERNANCE MODELS (approval / alert / control / audit / security)
# ─────────────────────────────────────────────────────────────


class ApprovalRequestModel(Base):
    __tablename__ = "agent_approval_requests"

    approval_id = Column(String(64), primary_key=True)
    requested_by = Column(String(64), nullable=False, index=True)
    requested_by_type = Column(String(32), nullable=False)
    action = Column(String(120), nullable=False)
    target = Column(String(255), nullable=True)
    reason = Column(Text, nullable=False)
    risk_level = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="pending", index=True)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    decided_by = Column(String(64), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    decision_reason = Column(Text, nullable=True)

    __table_args__ = (Index("ix_agent_approval_status_created", "status", "created_at"),)


class AlertRecordModel(Base):
    __tablename__ = "agent_alert_records"

    alert_id = Column(String(64), primary_key=True)
    category = Column(String(64), nullable=False, index=True)
    severity = Column(String(16), nullable=False, index=True)
    source = Column(String(64), nullable=False)
    actor_id = Column(String(64), nullable=True, index=True)
    target = Column(String(255), nullable=True)
    event = Column(String(120), nullable=False)
    evidence = Column(Text, nullable=True)
    status = Column(String(16), nullable=False, default="open", index=True)
    created_at = Column(DateTime, nullable=False, index=True)
    assigned_to = Column(String(64), nullable=True)
    resolution = Column(Text, nullable=True)


class ControlStateModel(Base):
    __tablename__ = "agent_control_state"

    id = Column(String(16), primary_key=True, default="current")
    mode = Column(String(32), nullable=False, default="normal")
    changed_at = Column(DateTime, nullable=False)
    changed_by = Column(String(64), nullable=False)
    reason = Column(Text, nullable=False)


class AgentAuditRecordModel(Base):
    __tablename__ = "agent_audit_records"

    audit_id = Column(String(64), primary_key=True)
    actor_id = Column(String(64), nullable=True, index=True)
    actor_type = Column(String(32), nullable=False)
    action = Column(String(64), nullable=False, index=True)
    subject_type = Column(String(64), nullable=True)
    subject_id = Column(String(64), nullable=True)
    occurred_at = Column(DateTime, nullable=False, index=True)
    success = Column(Boolean, nullable=False, default=True)
    reason = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)


class SecurityEventModel(Base):
    __tablename__ = "agent_security_events"

    event_id = Column(String(64), primary_key=True)
    kind = Column(String(16), nullable=False, index=True)
    pattern = Column(String(64), nullable=False, index=True)
    source = Column(String(64), nullable=True)
    actor_id = Column(String(64), nullable=True, index=True)
    target = Column(String(255), nullable=True)
    evidence = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    source_observation_id = Column(String(64), nullable=True)
    occurred_at = Column(DateTime, nullable=False, index=True)
