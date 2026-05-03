import uuid
from sqlalchemy import String, Text, Float, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKey


class Signal(Base, UUIDPrimaryKey, TimestampMixin):
    """Raw signal discovered by Scout agent."""
    __tablename__ = "signals"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.id", ondelete="SET NULL"), index=True
    )
    domain: Mapped[str] = mapped_column(String(50), nullable=False, default="lkm")

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str | None] = mapped_column(String(2000))
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # patent/scientific/news/...

    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    relevance_rationale: Mapped[str | None] = mapped_column(Text)

    raw_data: Mapped[dict | None] = mapped_column(JSON)
    is_processed: Mapped[bool] = mapped_column(default=False)
    is_duplicate: Mapped[bool] = mapped_column(default=False)

    hypothesis_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hypotheses.id", ondelete="SET NULL"), index=True
    )
