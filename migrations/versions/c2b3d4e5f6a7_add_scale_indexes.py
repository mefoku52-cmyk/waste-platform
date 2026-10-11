"""add scale indexes (idempotent)

Revision ID: c2b3d4e5f6a7
Revises: b1a2c3d4e5f6
Create Date: 2026-10-11

Presun povodneho orphan suboru migrations/20260817_scale_indexes.sql
(lezi mimo migrations/versions/, takze ho Alembic nikdy nespustil) do
riadnej migracie. Vsetky indexy pouzivaju IF NOT EXISTS, aby migracia
presla aj na DB, kde ich uz vytvoril manualny raw SQL bootstrap.
"""

from alembic import op

revision = "c2b3d4e5f6a7"
down_revision = "b1a2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_listings_status ON listings (status);
        CREATE INDEX IF NOT EXISTS ix_listings_company_id ON listings (company_id);
        CREATE INDEX IF NOT EXISTS ix_listings_material_type ON listings (material_type);
        CREATE INDEX IF NOT EXISTS ix_listings_location ON listings (location);
        CREATE INDEX IF NOT EXISTS ix_listings_created_at ON listings (created_at DESC);
        CREATE INDEX IF NOT EXISTS ix_listings_status_material ON listings (status, material_type);
        CREATE INDEX IF NOT EXISTS ix_listings_status_company ON listings (status, company_id);
        CREATE INDEX IF NOT EXISTS ix_inquiries_listing_id ON inquiries (listing_id);
        CREATE INDEX IF NOT EXISTS ix_inquiries_company_id ON inquiries (company_id);
        CREATE INDEX IF NOT EXISTS ix_inquiries_status ON inquiries (status);
        CREATE INDEX IF NOT EXISTS ix_inquiries_created_at ON inquiries (created_at DESC);
        CREATE INDEX IF NOT EXISTS ix_inquiries_company_status ON inquiries (company_id, status);
        CREATE INDEX IF NOT EXISTS ix_documents_company_id ON documents (company_id);
        CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications (user_id);
        CREATE INDEX IF NOT EXISTS ix_notifications_created_at ON notifications (created_at DESC);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS ix_listings_status;
        DROP INDEX IF EXISTS ix_listings_company_id;
        DROP INDEX IF EXISTS ix_listings_material_type;
        DROP INDEX IF EXISTS ix_listings_location;
        DROP INDEX IF EXISTS ix_listings_created_at;
        DROP INDEX IF EXISTS ix_listings_status_material;
        DROP INDEX IF EXISTS ix_listings_status_company;
        DROP INDEX IF EXISTS ix_inquiries_listing_id;
        DROP INDEX IF EXISTS ix_inquiries_company_id;
        DROP INDEX IF EXISTS ix_inquiries_status;
        DROP INDEX IF EXISTS ix_inquiries_created_at;
        DROP INDEX IF EXISTS ix_inquiries_company_status;
        DROP INDEX IF EXISTS ix_documents_company_id;
        DROP INDEX IF EXISTS ix_notifications_user_id;
        DROP INDEX IF EXISTS ix_notifications_created_at;
        """
    )
