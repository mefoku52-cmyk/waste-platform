"""add company_pages and company_photos tables

Revision ID: d3c4e5f6a7b8
Revises: c2b3d4e5f6a7
Create Date: 2026-10-14

Verejné firemné stránky (CMEP): jedna stránka na firmu (``company_id``
UNIQUE, ``slug`` UNIQUE) + fotogaléria (``company_photos``).
Kanonickým zdrojom firemných údajov ostáva tabuľka ``companies``.

Každý DDL prikaz je samostatny (asyncpg nezvladne viac prikazov v jednom
prepared statemente — viz migracia c2b3d4e5f6a7).
"""

import sqlalchemy as sa
from alembic import op

revision = "d3c4e5f6a7b8"
down_revision = "c2b3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_pages",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="draft"),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("tagline", sa.String(length=255), nullable=True),
        sa.Column("about_short", sa.String(length=600), nullable=True),
        sa.Column("about_long", sa.Text(), nullable=True),
        sa.Column("services", sa.Text(), nullable=True),
        sa.Column("specialization", sa.Text(), nullable=True),
        sa.Column("certifications", sa.Text(), nullable=True),
        sa.Column("opening_hours", sa.String(length=500), nullable=True),
        sa.Column("languages", sa.String(length=255), nullable=True),
        sa.Column("categories", sa.String(length=500), nullable=True),
        sa.Column("area", sa.String(length=255), nullable=True),
        sa.Column("public_email", sa.String(length=255), nullable=True),
        sa.Column("public_phone", sa.String(length=64), nullable=True),
        sa.Column("public_website", sa.String(length=512), nullable=True),
        sa.Column("seo_title", sa.String(length=255), nullable=True),
        sa.Column("seo_description", sa.String(length=320), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by_user_id", sa.String(length=36), nullable=True),
    )
    op.create_index("ix_company_pages_company_id", "company_pages", ["company_id"], unique=True)
    op.create_index("ix_company_pages_slug", "company_pages", ["slug"], unique=True)
    op.create_index("ix_company_pages_status", "company_pages", ["status"])

    op.create_table(
        "company_photos",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("file_url", sa.String(length=1024), nullable=False),
        sa.Column("caption", sa.String(length=500), nullable=True),
        sa.Column("alt_text", sa.String(length=500), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by_user_id", sa.String(length=36), nullable=True),
    )
    op.create_index("ix_company_photos_company_id", "company_photos", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_company_photos_company_id", table_name="company_photos")
    op.drop_table("company_photos")
    op.drop_index("ix_company_pages_status", table_name="company_pages")
    op.drop_index("ix_company_pages_slug", table_name="company_pages")
    op.drop_index("ix_company_pages_company_id", table_name="company_pages")
    op.drop_table("company_pages")
