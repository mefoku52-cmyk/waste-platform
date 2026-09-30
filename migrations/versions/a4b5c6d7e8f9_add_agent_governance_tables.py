"""add agent_platform governance tables (approval/alert/control/audit/security)

Revision ID: a4b5c6d7e8f9
Revises: a3c4d5e6f7a8
Create Date: 2026-09-27
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "a4b5c6d7e8f9"
down_revision = "a3c4d5e6f7a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = set(inspector.get_table_names())

    if "agent_approval_requests" not in tables:
        op.create_table(
            "agent_approval_requests",
            sa.Column("approval_id", sa.String(length=64), primary_key=True),
            sa.Column("requested_by", sa.String(length=64), nullable=False),
            sa.Column("requested_by_type", sa.String(length=32), nullable=False),
            sa.Column("action", sa.String(length=120), nullable=False),
            sa.Column("target", sa.String(length=255), nullable=True),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("risk_level", sa.String(length=32), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("decided_by", sa.String(length=64), nullable=True),
            sa.Column("decided_at", sa.DateTime(), nullable=True),
            sa.Column("decision_reason", sa.Text(), nullable=True),
        )
        op.create_index(
            "ix_agent_approval_requested_by", "agent_approval_requests", ["requested_by"]
        )
        op.create_index("ix_agent_approval_status", "agent_approval_requests", ["status"])
        op.create_index(
            "ix_agent_approval_status_created",
            "agent_approval_requests",
            ["status", "created_at"],
        )

    if "agent_alert_records" not in tables:
        op.create_table(
            "agent_alert_records",
            sa.Column("alert_id", sa.String(length=64), primary_key=True),
            sa.Column("category", sa.String(length=64), nullable=False),
            sa.Column("severity", sa.String(length=16), nullable=False),
            sa.Column("source", sa.String(length=64), nullable=False),
            sa.Column("actor_id", sa.String(length=64), nullable=True),
            sa.Column("target", sa.String(length=255), nullable=True),
            sa.Column("event", sa.String(length=120), nullable=False),
            sa.Column("evidence", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("assigned_to", sa.String(length=64), nullable=True),
            sa.Column("resolution", sa.Text(), nullable=True),
        )
        op.create_index("ix_agent_alert_category", "agent_alert_records", ["category"])
        op.create_index("ix_agent_alert_severity", "agent_alert_records", ["severity"])
        op.create_index("ix_agent_alert_actor_id", "agent_alert_records", ["actor_id"])
        op.create_index("ix_agent_alert_status", "agent_alert_records", ["status"])
        op.create_index("ix_agent_alert_created_at", "agent_alert_records", ["created_at"])

    if "agent_control_state" not in tables:
        op.create_table(
            "agent_control_state",
            sa.Column("id", sa.String(length=16), primary_key=True),
            sa.Column("mode", sa.String(length=32), nullable=False, server_default="normal"),
            sa.Column("changed_at", sa.DateTime(), nullable=False),
            sa.Column("changed_by", sa.String(length=64), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
        )

    if "agent_audit_records" not in tables:
        op.create_table(
            "agent_audit_records",
            sa.Column("audit_id", sa.String(length=64), primary_key=True),
            sa.Column("actor_id", sa.String(length=64), nullable=True),
            sa.Column("actor_type", sa.String(length=32), nullable=False),
            sa.Column("action", sa.String(length=64), nullable=False),
            sa.Column("subject_type", sa.String(length=64), nullable=True),
            sa.Column("subject_id", sa.String(length=64), nullable=True),
            sa.Column("occurred_at", sa.DateTime(), nullable=False),
            sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("reason", sa.String(length=255), nullable=True),
            sa.Column("details", sa.Text(), nullable=True),
        )
        op.create_index("ix_agent_audit_actor_id", "agent_audit_records", ["actor_id"])
        op.create_index("ix_agent_audit_action", "agent_audit_records", ["action"])
        op.create_index("ix_agent_audit_occurred_at", "agent_audit_records", ["occurred_at"])

    if "agent_security_events" not in tables:
        op.create_table(
            "agent_security_events",
            sa.Column("event_id", sa.String(length=64), primary_key=True),
            sa.Column("kind", sa.String(length=16), nullable=False),
            sa.Column("pattern", sa.String(length=64), nullable=False),
            sa.Column("source", sa.String(length=64), nullable=True),
            sa.Column("actor_id", sa.String(length=64), nullable=True),
            sa.Column("target", sa.String(length=255), nullable=True),
            sa.Column("evidence", sa.Text(), nullable=True),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("source_observation_id", sa.String(length=64), nullable=True),
            sa.Column("occurred_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_agent_security_kind", "agent_security_events", ["kind"])
        op.create_index("ix_agent_security_pattern", "agent_security_events", ["pattern"])
        op.create_index("ix_agent_security_actor_id", "agent_security_events", ["actor_id"])
        op.create_index("ix_agent_security_occurred_at", "agent_security_events", ["occurred_at"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = set(inspector.get_table_names())

    for t in (
        "agent_security_events",
        "agent_audit_records",
        "agent_control_state",
        "agent_alert_records",
        "agent_approval_requests",
    ):
        if t in tables:
            op.drop_table(t)
