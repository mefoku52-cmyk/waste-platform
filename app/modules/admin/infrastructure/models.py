"""admin database models."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.shared.infrastructure.db.base import Base


class AdminAuditEntryModel(Base):
    __tablename__ = "admin_audit_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_user_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(120), nullable=False)
    target_type = Column(String(120), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=True)
    details = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="success")
    created_at = Column(DateTime, default=lambda: datetime.now())
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(),
        onupdate=lambda: datetime.now(),
    )
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    updated_by_user_id = Column(UUID(as_uuid=True), nullable=True)
