"""Company model."""

from typing import Optional, List
from sqlalchemy import Column, String, Text, Boolean, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel
from app.models.user import user_companies


class CompanyType(str, enum.Enum):
    """Company types."""
    WASTE_PRODUCER = "waste_producer"  # Producent odpadu
    WASTE_COLLECTOR = "waste_collector"  # Zberateľ odpadu
    WASTE_PROCESSOR = "waste_processor"  # Spracovateľ odpadu
    RECYCLER = "recycler"  # Recyklátor
    BROKER = "broker"  # Sprostredkovateľ
    LOGISTICS = "logistics"  # Logistika


class CompanyStatus(str, enum.Enum):
    """Company status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


class Company(BaseModel):
    """Company model."""
    
    __tablename__ = "companies"
    
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    company_type = Column(Enum(CompanyType), nullable=False)
    status = Column(Enum(CompanyStatus), default=CompanyStatus.PENDING, nullable=False)
    
    ico = Column(String(20), unique=True, nullable=True)  # IČO
    dic = Column(String(20), nullable=True)  # DIČ
    ic_dph = Column(String(20), nullable=True)  # IČ DPH
    
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    
    logo_url = Column(String(500), nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    users = relationship(
        "User",
        secondary=user_companies,
        back_populates="companies",
        lazy="selectin"
    )
    
    listings = relationship(
        "Listing",
        back_populates="company",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    memberships = relationship(
        "Membership",
        back_populates="company",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Company {self.name}>"
