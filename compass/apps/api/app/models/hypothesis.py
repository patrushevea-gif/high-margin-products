import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, Float, JSON, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKey


class Hypothesis(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "hypotheses"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    created_by: Mapped[str | None] = mapped_column(String(255))

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    short_description: Mapped[str] = mapped_column(Text, nullable=False)
    long_description: Mapped[str | None] = mapped_column(Text)

    domain: Mapped[str] = mapped_column(String(50), nullable=False, default="lkm")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")

    curator_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    # Hypothesis DNA — stored as JSONB for flexibility
    technical: Mapped[dict | None] = mapped_column(JSON)
    market: Mapped[dict | None] = mapped_column(JSON)
    economics: Mapped[dict | None] = mapped_column(JSON)
    risks: Mapped[dict | None] = mapped_column(JSON)

    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    overall_score: Mapped[float | None] = mapped_column(Float)

    source_signals: Mapped[list] = mapped_column(JSON, default=list)
    related_hypotheses: Mapped[list] = mapped_column(JSON, default=list)
    resurrection_triggers: Mapped[list] = mapped_column(JSON, default=list)

    war_room_active: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_confirm_override: Mapped[bool | None] = mapped_column(Boolean)

    last_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tags: Mapped[list] = mapped_column(JSON, default=list)

    evaluations: Mapped[list["HypothesisEvaluation"]] = relationship(
        back_populates="hypothesis", cascade="all, delete-orphan"
    )


class HypothesisEvaluation(Base, UUIDPrimaryKey, TimestampMixin):
    """Immutable snapshot of an agent evaluation — Time Machine row."""
    __tablename__ = "hypothesis_evaluations"

    hypothesis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hypotheses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    delta: Mapped[dict | None] = mapped_column(JSON)

    hypothesis: Mapped["Hypothesis"] = relationship(back_populates="evaluations")
