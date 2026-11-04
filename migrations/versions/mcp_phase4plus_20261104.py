"""MCP Phase 4+: OAuth, approvals, audit and resumable streams.
Revision ID: mcp_phase4plus_20261104
Revises: set the actual preceding revision in the integration checkout.
"""

import sqlalchemy as sa
from alembic import op

revision = "mcp_phase4plus_20261104"
down_revision = "c7e9a2b4d6f1"
branch_labels = None
depends_on = None


def upgrade():
    json_type = sa.JSON()
    op.create_table(
        "mcp_oauth_clients",
        sa.Column("client_id", sa.String(80), primary_key=True),
        sa.Column("client_name", sa.String(120), nullable=False),
        sa.Column("redirect_uris", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "mcp_oauth_requests",
        sa.Column("request_id", sa.String(64), primary_key=True),
        sa.Column("client_id", sa.String(80), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("redirect_uri", sa.Text, nullable=False),
        sa.Column("code_challenge", sa.String(128), nullable=False),
        sa.Column("state", sa.String(512), nullable=False),
        sa.Column("scopes", json_type, nullable=False),
        sa.Column("company_ids", json_type, nullable=False),
        sa.Column("resource", sa.Text, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_mcp_oauth_requests_client_id", "mcp_oauth_requests", ["client_id"])
    op.create_index("ix_mcp_oauth_requests_user_id", "mcp_oauth_requests", ["user_id"])
    op.create_table(
        "mcp_oauth_codes",
        sa.Column("code_hash", sa.String(64), primary_key=True),
        sa.Column("request_id", sa.String(64), nullable=False, unique=True),
        sa.Column("client_id", sa.String(80), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("redirect_uri", sa.Text, nullable=False),
        sa.Column("code_challenge", sa.String(128), nullable=False),
        sa.Column("scopes", json_type, nullable=False),
        sa.Column("company_ids", json_type, nullable=False),
        sa.Column("resource", sa.Text, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "mcp_oauth_tokens",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("client_id", sa.String(80), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("company_ids", json_type, nullable=False),
        sa.Column("scopes", json_type, nullable=False),
        sa.Column("resource", sa.Text, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_mcp_oauth_tokens_user_id", "mcp_oauth_tokens", ["user_id"])
    op.create_index("ix_mcp_oauth_token_expiry", "mcp_oauth_tokens", ["expires_at"])
    op.create_table(
        "mcp_approval_records",
        sa.Column("approval_id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), nullable=False),
        sa.Column("requester_id", sa.String(36), nullable=False),
        sa.Column("approver_id", sa.String(36)),
        sa.Column("tool_name", sa.String(120), nullable=False),
        sa.Column("arguments", json_type, nullable=False),
        sa.Column("arguments_hash", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("capability_hash", sa.String(64)),
        sa.Column("lease_until", sa.DateTime(timezone=True)),
        sa.Column("result", json_type),
        sa.Column("failure_code", sa.String(80)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "company_id",
            "requester_id",
            "idempotency_key",
            name="uq_mcp_approval_tenant_idempotency",
        ),
    )
    for col in ("company_id", "requester_id", "status"):
        op.create_index(f"ix_mcp_approval_records_{col}", "mcp_approval_records", [col])
    op.create_table(
        "mcp_audit_log",
        sa.Column("audit_id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("approval_id", sa.String(36)),
        sa.Column("tool_name", sa.String(120), nullable=False),
        sa.Column("outcome", sa.String(32), nullable=False),
        sa.Column("detail_code", sa.String(80)),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    for col in ("company_id", "actor_id", "approval_id"):
        op.create_index(f"ix_mcp_audit_log_{col}", "mcp_audit_log", [col])
    op.create_table(
        "mcp_streams",
        sa.Column("stream_id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("company_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_event_id", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("ix_mcp_streams_user_id", "mcp_streams", ["user_id"])
    op.create_index("ix_mcp_streams_company_id", "mcp_streams", ["company_id"])
    op.create_table(
        "mcp_stream_events",
        sa.Column("event_pk", sa.String(36), primary_key=True),
        sa.Column("stream_id", sa.String(64), nullable=False),
        sa.Column("event_id", sa.String(80), nullable=False, unique=True),
        sa.Column("sequence", sa.Integer, nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("payload", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("stream_id", "sequence", name="uq_mcp_stream_sequence"),
    )
    op.create_index("ix_mcp_stream_events_stream_id", "mcp_stream_events", ["stream_id"])


def downgrade():
    for table in (
        "mcp_stream_events",
        "mcp_streams",
        "mcp_audit_log",
        "mcp_approval_records",
        "mcp_oauth_tokens",
        "mcp_oauth_codes",
        "mcp_oauth_requests",
        "mcp_oauth_clients",
    ):
        op.drop_table(table)
