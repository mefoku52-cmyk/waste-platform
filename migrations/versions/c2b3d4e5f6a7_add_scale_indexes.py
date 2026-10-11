"""add scale indexes (idempotent)

Revision ID: c2b3d4e5f6a7
Revises: b1a2c3d4e5f6
Create Date: 2026-10-11

Presun povodneho orphan suboru migrations/20260817_scale_indexes.sql
(lezi mimo migrations/versions/, takze ho Alembic nikdy nespustil) do
riadnej migracie. Vsetky indexy pouzivaju IF NOT EXISTS, aby migracia
presla aj na DB, kde ich uz vytvoril manualny raw SQL bootstrap.

Kazdy CREATE INDEX je v samostatnom op.execute() volani — asyncpg
(PostgreSQL) odmieta viacero SQL prikazov v jednom prepared statemente
(cannot insert multiple commands into a prepared statement).
"""

from alembic import op

revision = "c2b3d4e5f6a7"
down_revision = "b1a2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS ix_listings_status ON listings (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_listings_company_id ON listings (company_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_listings_material_type ON listings (material_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_listings_location ON listings (location)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_listings_created_at ON listings (created_at DESC)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_listings_status_material ON listings (status, material_type)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_listings_status_company ON listings (status, company_id)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_inquiries_listing_id ON inquiries (listing_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_inquiries_company_id ON inquiries (company_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_inquiries_status ON inquiries (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_inquiries_created_at ON inquiries (created_at DESC)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_inquiries_company_status ON inquiries (company_id, status)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_documents_company_id ON documents (company_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications (user_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_notifications_created_at ON notifications (created_at DESC)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_listings_status")
    op.execute("DROP INDEX IF EXISTS ix_listings_company_id")
    op.execute("DROP INDEX IF EXISTS ix_listings_material_type")
    op.execute("DROP INDEX IF EXISTS ix_listings_location")
    op.execute("DROP INDEX IF EXISTS ix_listings_created_at")
    op.execute("DROP INDEX IF EXISTS ix_listings_status_material")
    op.execute("DROP INDEX IF EXISTS ix_listings_status_company")
    op.execute("DROP INDEX IF EXISTS ix_inquiries_listing_id")
    op.execute("DROP INDEX IF EXISTS ix_inquiries_company_id")
    op.execute("DROP INDEX IF EXISTS ix_inquiries_status")
    op.execute("DROP INDEX IF EXISTS ix_inquiries_created_at")
    op.execute("DROP INDEX IF EXISTS ix_inquiries_company_status")
    op.execute("DROP INDEX IF EXISTS ix_documents_company_id")
    op.execute("DROP INDEX IF EXISTS ix_notifications_user_id")
    op.execute("DROP INDEX IF EXISTS ix_notifications_created_at")
