"""Membership model."""

from sqlalchemy import Column, Enum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class MembershipRole(str, enum.Enum):
    """Membership roles."""
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"


class MembershipStatus(str, enum.Enum):
    """Membership status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class Membership(BaseModel):
    """Membership model."""
    
    __tablename__ = "memberships"
    
    role = Column(Enum(MembershipRole), default=MembershipRole.MEMBER, nullable=False)
    status = Column(Enum(MembershipStatus), default=MembershipStatus.PENDING, nullable=False, index=True)
    
    joined_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", lazy="selectin")
    company = relationship("Company", back_populates="memberships", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<Membership {self.user_id} in {self.company_id}>"
