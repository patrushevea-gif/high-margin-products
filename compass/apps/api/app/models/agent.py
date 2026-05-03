import uuid
from datetime import datetime
from sqlalchemy import String, Text, Float, Integer, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKey


class AgentSettings(Base, UUIDPrimaryKey, TimestampMixin):
    """Per-agent configuration, versioned."""
    __tablename__ = "agent_settings"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    agent_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    model: Mapped[str] = mapped_column(String(100), default="claude-sonnet-4-6")
    temperature: Mapped[float] = mapped_column(Float, default=0.3)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096)

    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    system_prompt_version: Mapped[int] = mapped_column(Integer, default=1)

    allowed_tools: Mapped[list] = mapped_column(JSON, default=list)
    auto_confirm: Mapped[bool] = mapped_column(Boolean, default=False)
    cost_limit_per_run_usd: Mapped[float] = mapped_column(Float, default=1.0)
    schedule: Mapped[str | None] = mapped_column(String(100))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    prompt_history: Mapped[list] = mapped_column(JSON, default=list)


class AgentRun(Base, UUIDPrimaryKey, TimestampMixin):
    """One execution of an agent on a hypothesis or source."""
    __tablename__ = "agent_runs"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    agent_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    hypothesis_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hypotheses.id", ondelete="SET NULL"), index=True
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    status: Mapped[str] = mapped_column(String(30), default="running")  # running/completed/failed
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    input_snapshot: Mapped[dict | None] = mapped_column(JSON)
    output_snapshot: Mapped[dict | None] = mapped_column(JSON)
    reasoning_chain: Mapped[list | None] = mapped_column(JSON)

    tokens_input: Mapped[int] = mapped_column(Integer, default=0)
    tokens_output: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    error: Mapped[str | None] = mapped_column(Text)


class ToolLog(Base, UUIDPrimaryKey, TimestampMixin):
    """Every agent tool call, for full traceability."""
    __tablename__ = "tools_log"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="CASCADE"), index=True
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    input: Mapped[dict] = mapped_column(JSON, nullable=False)
    output: Mapped[dict | None] = mapped_column(JSON)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
