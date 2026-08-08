"""analytics database models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.shared.infrastructure.db.base import Base


class AnalyticsEventModel(Base):
    __tablename__ = "analytics_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(120), nullable=False)
    entity_type = Column(String(120), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    company_id = Column(UUID(as_uuid=True), nullable=True)
    event_metadata = Column(Text, nullable=True)
    recorded_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    updated_by_user_id = Column(UUID(as_uuid=True), nullable=True)
