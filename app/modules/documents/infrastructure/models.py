"""documents database models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.shared.infrastructure.db.base import Base


class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    document_type = Column(String(120), nullable=False)
    file_url = Column(String(1024), nullable=False)
    company_id = Column(UUID(as_uuid=True), nullable=False)
    listing_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(32), nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    updated_by_user_id = Column(UUID(as_uuid=True), nullable=True)
