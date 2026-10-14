"""add company_reviews table

Revision ID: e4d5f6a7b8c9
Revises: d3c4e5f6a7b8
Create Date: 2026-10-14

Recenzie firiem (CMEP): jedna recenzia na používateľa a firmu (UNIQUE),
stav moderácie ``pending``/``approved``/``rejected``. Verejne sa zobrazujú
len ``approved``.
"""

import sqlalchemy as sa
from alembic import op

revision = "e4d5f6a7b8c9"
down_revision = "d3c4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_reviews",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("author_user_id", sa.String(length=36), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("moderated_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("moderated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by_user_id", sa.String(length=36), nullable=True),
        sa.UniqueConstraint(
            "company_id", "author_user_id", name="uq_company_reviews_company_author"
        ),
    )
    op.create_index("ix_company_reviews_company_id", "company_reviews", ["company_id"])
    op.create_index("ix_company_reviews_author_user_id", "company_reviews", ["author_user_id"])
    op.create_index("ix_company_reviews_status", "company_reviews", ["status"])
    op.create_index(
        "ix_company_reviews_company_status", "company_reviews", ["company_id", "status"]
    )


def downgrade() -> None:
    op.drop_index("ix_company_reviews_company_status", table_name="company_reviews")
    op.drop_index("ix_company_reviews_status", table_name="company_reviews")
    op.drop_index("ix_company_reviews_author_user_id", table_name="company_reviews")
    op.drop_index("ix_company_reviews_company_id", table_name="company_reviews")
    op.drop_table("company_reviews")
