"""Compliance SQLAlchemy models."""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from app.shared.infrastructure.db.base import Base


class ComplianceRecordModel(Base):
    __tablename__ = "compliance_records"

    id = Column(UUID(as_uuid=True), primary_key=True)
    company_id = Column(UUID(as_uuid=True), nullable=False)
    regulation_type = Column(String(120), nullable=False)
    document_ref = Column(String(255), nullable=True)
    valid_until = Column(DateTime, nullable=True)
    notes = Column(String, nullable=True)
    status = Column(String(32), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    created_by_user_id = Column(UUID(as_uuid=True))
    updated_by_user_id = Column(UUID(as_uuid=True))
