"""add activity_events table (idempotent)

Revision ID: b1a2c3d4e5f6
Revises: d5e6f7a8b9c0
Create Date: 2026-10-11

Poznamka: tabulka uz existuje v prostrediach, ktore boli bootstrapovane
raw SQL skriptami (activity_events.sql / render_missing_tables.sql).
Migracia je preto idempotentna (CREATE TABLE IF NOT EXISTS), aby presla
na cerstvej aj na uz provisionovanej DB. Schema je identicka s modelom
app/modules/events/infrastructure/models.py.
"""

from alembic import op

revision = "b1a2c3d4e5f6"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS activity_events (
            id uuid PRIMARY KEY,
            event_type varchar(64) NOT NULL,
            actor_user_id varchar(36),
            company_id varchar(36),
            listing_id varchar(36),
            payload text,
            created_at timestamp NOT NULL
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS activity_events")
