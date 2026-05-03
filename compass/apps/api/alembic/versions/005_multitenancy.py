"""Multitenancy: organizations, members, org_id on all tenant-scoped tables

Revision ID: 005
Revises: 004
Create Date: 2026-05-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── organizations ──────────────────────────────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("plan", sa.String(50), nullable=False, server_default="starter"),
        sa.Column("hypotheses_limit", sa.Integer, server_default="10"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("settings", sa.JSON, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"])

    # ── organization_members ───────────────────────────────────────────────────
    op.create_table(
        "organization_members",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("user_id", sa.String(255), nullable=False),   # Supabase auth.users UUID as string
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="researcher"),
        sa.Column("invited_by", sa.String(255)),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_org_members_org_id",  "organization_members", ["organization_id"])
    op.create_index("ix_org_members_user_id", "organization_members", ["user_id"])
    op.create_unique_constraint(
        "uq_org_member", "organization_members", ["organization_id", "user_id"]
    )

    # ── audit_log ──────────────────────────────────────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("user_id",  sa.String(255), nullable=False),
        sa.Column("email",    sa.String(255), nullable=False),
        sa.Column("action",   sa.String(100), nullable=False),   # e.g. hypothesis.created
        sa.Column("resource_type", sa.String(100)),              # hypothesis / source / agent
        sa.Column("resource_id",   sa.String(255)),
        sa.Column("meta",     sa.JSON, server_default="{}"),
        sa.Column("ip",       sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_audit_log_org_created",
                    "audit_log", ["organization_id", "created_at"])

    # ── add org_id to tenant-scoped tables ─────────────────────────────────────
    for table in ("hypotheses", "signals", "sources", "agent_runs"):
        op.add_column(table, sa.Column(
            "organization_id", UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=True,   # nullable so existing rows survive migration
        ))
        op.create_index(f"ix_{table}_org_id", table, ["organization_id"])

    # agent_settings are per-org too (each org can tune their own agents)
    op.add_column("agent_settings", sa.Column(
        "organization_id", UUID(as_uuid=True),
        sa.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    ))
    op.create_index("ix_agent_settings_org_id", "agent_settings", ["organization_id"])

    # Drop the now-incorrect unique constraint on agent_name (was global, now per-org)
    op.drop_index("ix_agent_settings_agent_name", table_name="agent_settings")
    op.drop_constraint("agent_settings_agent_name_key", "agent_settings", type_="unique")

    # created_by on hypotheses (which user triggered the hypothesis)
    op.add_column("hypotheses", sa.Column(
        "created_by", sa.String(255), nullable=True
    ))


def downgrade() -> None:
    op.drop_column("hypotheses", "created_by")
    for table in ("hypotheses", "signals", "sources", "agent_runs", "agent_settings"):
        op.drop_index(f"ix_{table}_org_id", table_name=table)
        op.drop_column(table, "organization_id")

    # Restore agent_settings unique on agent_name (single-tenant)
    op.create_unique_constraint(
        "agent_settings_agent_name_key", "agent_settings", ["agent_name"]
    )
    op.create_index("ix_agent_settings_agent_name", "agent_settings", ["agent_name"])

    op.drop_table("audit_log")
    op.drop_table("organization_members")
    op.drop_table("organizations")
