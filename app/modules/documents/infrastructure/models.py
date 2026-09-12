"""Documents SQLAlchemy models."""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from app.shared.infrastructure.db.base import Base


class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True)
    title = Column(String(255), nullable=False)
    document_type = Column(String(120), nullable=False)
    file_url = Column(String(1024), nullable=False)
    company_id = Column(UUID(as_uuid=True), nullable=False)
    listing_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(32), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    created_by_user_id = Column(UUID(as_uuid=True))
    updated_by_user_id = Column(UUID(as_uuid=True))
