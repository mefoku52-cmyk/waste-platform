"""Reservation model."""

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class ReservationStatus(str, enum.Enum):
    """Reservation status."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Reservation(BaseModel):
    """Reservation model."""
    
    __tablename__ = "reservations"
    
    reservation_date = Column(DateTime(timezone=True), nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    
    status = Column(Enum(ReservationStatus), default=ReservationStatus.PENDING, nullable=False, index=True)
    
    quantity = Column(Numeric(10, 2), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Foreign keys
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Relationships
    listing = relationship("Listing", back_populates="reservations", lazy="selectin")
    user = relationship("User", lazy="selectin")
    company = relationship("Company", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<Reservation {self.id} for {self.listing_id}>"
