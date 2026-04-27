"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "sources",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("url_pattern", sa.String(2000)),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("domain", sa.String(50), nullable=False, server_default="lkm"),
        sa.Column("parsing_strategy", sa.String(50), server_default="ai"),
        sa.Column("selectors_hint", sa.Text),
        sa.Column("rate_limit_rpm", sa.Integer, server_default="10"),
        sa.Column("api_endpoint", sa.String(2000)),
        sa.Column("api_auth", JSON),
        sa.Column("api_schema_mapping", JSON),
        sa.Column("prefer_api", sa.Boolean, server_default="false"),
        sa.Column("schedule", sa.String(100), server_default="0 */6 * * *"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("last_run_at", sa.DateTime(timezone=True)),
        sa.Column("last_run_success", sa.Boolean),
        sa.Column("last_run_signals", sa.Integer, server_default="0"),
        sa.Column("tokens_used_month", sa.Integer, server_default="0"),
        sa.Column("cost_usd_month", sa.Float, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "hypotheses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("short_description", sa.Text, nullable=False),
        sa.Column("long_description", sa.Text),
        sa.Column("domain", sa.String(50), nullable=False, server_default="lkm"),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("curator_id", UUID(as_uuid=True)),
        sa.Column("technical", JSON),
        sa.Column("market", JSON),
        sa.Column("economics", JSON),
        sa.Column("risks", JSON),
        sa.Column("confidence_score", sa.Float, server_default="0"),
        sa.Column("overall_score", sa.Float),
        sa.Column("source_signals", JSON, server_default="'[]'"),
        sa.Column("related_hypotheses", JSON, server_default="'[]'"),
        sa.Column("resurrection_triggers", JSON, server_default="'[]'"),
        sa.Column("war_room_active", sa.Boolean, server_default="false"),
        sa.Column("auto_confirm_override", sa.Boolean),
        sa.Column("last_evaluated_at", sa.DateTime(timezone=True)),
        sa.Column("tags", JSON, server_default="'[]'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_hypotheses_domain", "hypotheses", ["domain"])
    op.create_index("ix_hypotheses_status", "hypotheses", ["status"])

    op.create_table(
        "signals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("source_id", UUID(as_uuid=True), sa.ForeignKey("sources.id", ondelete="SET NULL")),
        sa.Column("hypothesis_id", UUID(as_uuid=True), sa.ForeignKey("hypotheses.id", ondelete="SET NULL")),
        sa.Column("domain", sa.String(50), nullable=False, server_default="lkm"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("url", sa.String(2000)),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("relevance_score", sa.Float, server_default="0"),
        sa.Column("relevance_rationale", sa.Text),
        sa.Column("raw_data", JSON),
        sa.Column("is_processed", sa.Boolean, server_default="false"),
        sa.Column("is_duplicate", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_signals_source_id", "signals", ["source_id"])
    op.create_index("ix_signals_domain", "signals", ["domain"])

    op.create_table(
        "hypothesis_evaluations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("hypothesis_id", UUID(as_uuid=True), sa.ForeignKey("hypotheses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_name", sa.String(50), nullable=False),
        sa.Column("run_id", UUID(as_uuid=True)),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("snapshot", JSON, nullable=False),
        sa.Column("delta", JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_hypothesis_evaluations_hypothesis_id", "hypothesis_evaluations", ["hypothesis_id"])

    op.create_table(
        "agent_settings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("agent_name", sa.String(50), nullable=False, unique=True),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("model", sa.String(100), server_default="claude-sonnet-4-6"),
        sa.Column("temperature", sa.Float, server_default="0.3"),
        sa.Column("max_tokens", sa.Integer, server_default="4096"),
        sa.Column("system_prompt", sa.Text, nullable=False),
        sa.Column("system_prompt_version", sa.Integer, server_default="1"),
        sa.Column("allowed_tools", JSON, server_default="'[]'"),
        sa.Column("auto_confirm", sa.Boolean, server_default="false"),
        sa.Column("cost_limit_per_run_usd", sa.Float, server_default="1.0"),
        sa.Column("schedule", sa.String(100)),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("prompt_history", JSON, server_default="'[]'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "agent_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("agent_name", sa.String(50), nullable=False),
        sa.Column("hypothesis_id", UUID(as_uuid=True), sa.ForeignKey("hypotheses.id", ondelete="SET NULL")),
        sa.Column("source_id", UUID(as_uuid=True)),
        sa.Column("status", sa.String(30), server_default="running"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("input_snapshot", JSON),
        sa.Column("output_snapshot", JSON),
        sa.Column("reasoning_chain", JSON),
        sa.Column("tokens_input", sa.Integer, server_default="0"),
        sa.Column("tokens_output", sa.Integer, server_default="0"),
        sa.Column("cost_usd", sa.Float, server_default="0"),
        sa.Column("error", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_agent_runs_agent_name", "agent_runs", ["agent_name"])
    op.create_index("ix_agent_runs_hypothesis_id", "agent_runs", ["hypothesis_id"])

    op.create_table(
        "tools_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("input", JSON, nullable=False),
        sa.Column("output", JSON),
        sa.Column("duration_ms", sa.Integer, server_default="0"),
        sa.Column("error", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_tools_log_run_id", "tools_log", ["run_id"])


def downgrade() -> None:
    op.drop_table("tools_log")
    op.drop_table("agent_runs")
    op.drop_table("agent_settings")
    op.drop_table("hypothesis_evaluations")
    op.drop_table("signals")
    op.drop_table("hypotheses")
    op.drop_table("sources")
