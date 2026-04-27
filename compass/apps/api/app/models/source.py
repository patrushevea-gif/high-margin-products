from sqlalchemy import String, Text, Boolean, Integer, JSON, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKey


class Source(Base, UUIDPrimaryKey, TimestampMixin):
    """Data source definition — patents, news, scientific, competitors, etc."""
    __tablename__ = "sources"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url_pattern: Mapped[str | None] = mapped_column(String(2000))
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # patents/scientific/news/...
    domain: Mapped[str] = mapped_column(String(50), nullable=False, default="lkm")

    # AI parser config
    parsing_strategy: Mapped[str] = mapped_column(String(50), default="ai")  # ai | rss | api
    selectors_hint: Mapped[str | None] = mapped_column(Text)
    rate_limit_rpm: Mapped[int] = mapped_column(Integer, default=10)

    # Direct API config (filled when subscription exists)
    api_endpoint: Mapped[str | None] = mapped_column(String(2000))
    api_auth: Mapped[dict | None] = mapped_column(JSON)
    api_schema_mapping: Mapped[dict | None] = mapped_column(JSON)
    prefer_api: Mapped[bool] = mapped_column(Boolean, default=False)

    # Schedule (cron expression)
    schedule: Mapped[str] = mapped_column(String(100), default="0 */6 * * *")  # every 6 hours

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_run_success: Mapped[bool | None] = mapped_column(Boolean)
    last_run_signals: Mapped[int] = mapped_column(Integer, default=0)

    # Cost tracking
    tokens_used_month: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd_month: Mapped[float] = mapped_column(Float, default=0.0)
