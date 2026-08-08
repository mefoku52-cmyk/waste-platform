"""listings database models."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.shared.infrastructure.db.base import Base


class ListingsModel(Base):
    __tablename__ = "listings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    material_type = Column(String(120), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(32), nullable=False)
    price = Column(Float, nullable=True)
    currency = Column(String(8), nullable=False, default="EUR")
    condition = Column(String(120), nullable=False)
    location = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False, default="draft")
    company_id = Column(UUID(as_uuid=True), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    updated_by_user_id = Column(UUID(as_uuid=True), nullable=True)
