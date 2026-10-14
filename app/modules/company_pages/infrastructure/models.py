"""company_pages SQLAlchemy models.

``company_pages`` = jedna verejná stránka na firmu (``company_id`` UNIQUE),
``company_photos`` = galéria (viac fotiek na firmu).
"""

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.db.base import Base


class CompanyPageModel(Base):
    __tablename__ = "company_pages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, server_default="draft", default="draft"
    )

    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tagline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    about_short: Mapped[str | None] = mapped_column(String(600), nullable=True)
    about_long: Mapped[str | None] = mapped_column(Text, nullable=True)
    services: Mapped[str | None] = mapped_column(Text, nullable=True)
    specialization: Mapped[str | None] = mapped_column(Text, nullable=True)
    certifications: Mapped[str | None] = mapped_column(Text, nullable=True)
    opening_hours: Mapped[str | None] = mapped_column(String(500), nullable=True)
    languages: Mapped[str | None] = mapped_column(String(255), nullable=True)
    categories: Mapped[str | None] = mapped_column(String(500), nullable=True)
    area: Mapped[str | None] = mapped_column(String(255), nullable=True)

    public_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    public_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    public_website: Mapped[str | None] = mapped_column(String(512), nullable=True)

    seo_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(String(320), nullable=True)

    published_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class CompanyPhotoModel(Base):
    __tablename__ = "company_photos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    caption: Mapped[str | None] = mapped_column(String(500), nullable=True)
    alt_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="0", default=False
    )
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
