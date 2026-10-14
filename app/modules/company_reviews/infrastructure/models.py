"""company_reviews SQLAlchemy model."""

from sqlalchemy import DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.db.base import Base


class CompanyReviewModel(Base):
    __tablename__ = "company_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    author_user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, server_default="pending", default="pending"
    )
    moderated_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    moderated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    __table_args__ = (
        # Jedna recenzia na používateľa a firmu (predchádza spamu/duplicitám).
        UniqueConstraint("company_id", "author_user_id", name="uq_company_reviews_company_author"),
        Index("ix_company_reviews_company_status", "company_id", "status"),
    )
