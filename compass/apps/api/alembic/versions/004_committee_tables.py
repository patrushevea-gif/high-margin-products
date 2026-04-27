"""Add committee_sessions and committee_votes tables

Revision ID: 004
Revises: 003
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "committee_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("hypothesis_ids", JSON, nullable=False, server_default="'[]'"),
        sa.Column("status", sa.String(30), server_default="open"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True)),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("summary_markdown", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "committee_votes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", UUID(as_uuid=True),
                  sa.ForeignKey("committee_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hypothesis_id", UUID(as_uuid=True),
                  sa.ForeignKey("hypotheses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("voter_id", UUID(as_uuid=True)),
        sa.Column("vote", sa.String(30), nullable=False),
        sa.Column("comment", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_committee_votes_session_id", "committee_votes", ["session_id"])
    op.create_index("ix_committee_votes_hypothesis_id", "committee_votes", ["hypothesis_id"])


def downgrade() -> None:
    op.drop_table("committee_votes")
    op.drop_table("committee_sessions")
