from sqlalchemy import Boolean, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.db.base import Base


class CompanyModel(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    trading_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    registration_number: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, index=True
    )
    tax_identifier: Mapped[str | None] = mapped_column(String(128), nullable=True)
    vat_identifier: Mapped[str | None] = mapped_column(String(32), nullable=True)
    company_type: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    address_line_1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line_2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(64), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    seller_capability: Mapped[bool] = mapped_column(Boolean, nullable=False)
    buyer_capability: Mapped[bool] = mapped_column(Boolean, nullable=False)
    logistics_capability: Mapped[bool] = mapped_column(Boolean, nullable=False)
    accepted_material_types: Mapped[str | None] = mapped_column(String(512), nullable=True)
    verification_submitted_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verification_reviewed_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verification_reviewed_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    verified_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    rejected_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
