"""Listing model."""

from typing import Optional, List
from sqlalchemy import Column, String, Text, Numeric, Boolean, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class ListingType(str, enum.Enum):
    """Listing types."""
    WASTE = "waste"  # Odpad
    RAW_MATERIAL = "raw_material"  # Druhotná surovina
    SERVICE = "service"  # Služba


class ListingCategory(str, enum.Enum):
    """Listing categories."""
    PLASTIC = "plastic"  # Plasty
    PAPER = "paper"  # Papier
    GLASS = "glass"  # Sklo
    METAL = "metal"  # Kovy
    WOOD = "wood"  # Drevo
    TEXTILE = "textile"  # Textil
    ELECTRONICS = "electronics"  # Elektronika
    BATTERIES = "batteries"  # Batérie
    CHEMICAL = "chemical"  # Chemikálie
    BIOLOGICAL = "biological"  # Biologický odpad
    CONSTRUCTION = "construction"  # Stavebný odpad
    OTHER = "other"  # Iné


class ListingStatus(str, enum.Enum):
    """Listing status."""
    DRAFT = "draft"
    PENDING = "pending"
    ACTIVE = "active"
    RESERVED = "reserved"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ListingCondition(str, enum.Enum):
    """Listing condition."""
    NEW = "new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class Listing(BaseModel):
    """Listing model."""
    
    __tablename__ = "listings"
    
    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    listing_type = Column(Enum(ListingType), nullable=False)
    category = Column(Enum(ListingCategory), nullable=False, index=True)
    
    status = Column(Enum(ListingStatus), default=ListingStatus.DRAFT, nullable=False, index=True)
    condition = Column(Enum(ListingCondition), nullable=True)
    
    quantity = Column(Numeric(10, 2), nullable=True)
    unit = Column(String(50), nullable=True)  # kg, m3, ks, etc.
    
    price = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), default="EUR", nullable=True)
    
    location = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    
    is_negotiable = Column(Boolean, default=False)
    is_urgent = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    views_count = Column(Integer, default=0)
    favorites_count = Column(Integer, default=0)
    
    # Foreign keys
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="listings", lazy="selectin")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_listings", lazy="selectin")
    
    reservations = relationship(
        "Reservation",
        back_populates="listing",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Listing {self.title}>"
    
    @property
    def is_active(self) -> bool:
        """Check if listing is active."""
        return self.status == ListingStatus.ACTIVE
