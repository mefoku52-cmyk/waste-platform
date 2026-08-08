from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.db.base import Base


class CompanyMembershipModel(Base):
    __tablename__ = "company_memberships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    company_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    membership_role: Mapped[str] = mapped_column(String(64), nullable=False)
    is_primary_contact: Mapped[bool] = mapped_column(Boolean, nullable=False)
    invited_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    joined_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    left_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
