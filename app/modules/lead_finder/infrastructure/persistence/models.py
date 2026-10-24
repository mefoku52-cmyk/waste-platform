"""Lead finder database models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.shared.infrastructure.db.base import Base


class OutreachCandidateModel(Base):
    __tablename__ = "outreach_candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(255), nullable=False)
    ico = Column(String(32), nullable=True, index=True)
    city = Column(String(128), nullable=True, index=True)
    industry = Column(String(128), nullable=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(64), nullable=True)
    website = Column(String(512), nullable=True)
    source_url = Column(String(512), nullable=True)

    status = Column(String(32), nullable=False, default="new", server_default="new")

    draft_subject = Column(String(255), nullable=True)
    draft_body = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(),
        onupdate=lambda: datetime.now(),
    )
    approved_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    is_blacklisted = Column(Boolean, nullable=False, default=False, server_default="false")

    __table_args__ = (
        Index("ix_outreach_candidates_status", "status"),
        Index("ix_outreach_candidates_city_status", "city", "status"),
    )
