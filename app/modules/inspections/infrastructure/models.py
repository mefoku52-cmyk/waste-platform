"""inspections database models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.shared.infrastructure.db.base import Base


class InspectionModel(Base):
    __tablename__ = "inspections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(
        UUID(as_uuid=True),
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    room_id = Column(String(64), nullable=True, index=True)
    owner_user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    owner_company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    viewer_user_id = Column(UUID(as_uuid=True), nullable=True)
    viewer_company_id = Column(UUID(as_uuid=True), nullable=True)
    viewer_thread_id = Column(UUID(as_uuid=True), nullable=True)
    state = Column(String(32), nullable=False, default="created", server_default="created")
    consent_to_record = Column(Boolean, nullable=False, default=False, server_default="0")
    recording_consent_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now())
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(),
        onupdate=lambda: datetime.now(),
    )
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    updated_by_user_id = Column(UUID(as_uuid=True), nullable=True)


class InspectionEventModel(Base):
    """Eventy zo streamovacej sluzby (metadata only, ziaden medially obsah).

    Idempotencia: event_uid (vygeneruje streaming, napr. UUID) musi byt unikatny
    — duplikatny POST sa ignoruje (FALSE return), retry po sieti nezduplikuje.
    """

    __tablename__ = "inspection_events"
    __table_args__ = (UniqueConstraint("event_uid", name="uq_inspection_events_uid"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_uid = Column(String(64), nullable=False)
    inspection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type = Column(String(64), nullable=False, index=True)
    actor_user_id = Column(UUID(as_uuid=True), nullable=True)
    room_id = Column(String(64), nullable=True)
    role = Column(String(16), nullable=True)
    reason = Column(String(255), nullable=True)
    payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(), index=True)
