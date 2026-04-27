from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal


class SourceCreate(BaseModel):
    name: str = Field(..., max_length=200)
    url_pattern: str | None = None
    source_type: Literal["patents", "scientific", "news", "competitors", "raw_materials", "standards", "trends"]
    domain: str = "lkm"
    parsing_strategy: Literal["ai", "rss", "api"] = "ai"
    selectors_hint: str | None = None
    rate_limit_rpm: int = 10
    schedule: str = "0 */6 * * *"


class SourceUpdate(BaseModel):
    name: str | None = None
    url_pattern: str | None = None
    parsing_strategy: str | None = None
    rate_limit_rpm: int | None = None
    api_endpoint: str | None = None
    prefer_api: bool | None = None
    schedule: str | None = None
    is_active: bool | None = None


class SourceRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    name: str
    url_pattern: str | None
    source_type: str
    domain: str
    parsing_strategy: str
    rate_limit_rpm: int
    api_endpoint: str | None
    prefer_api: bool
    schedule: str
    is_active: bool
    last_run_at: datetime | None
    last_run_success: bool | None
    last_run_signals: int
    tokens_used_month: int
    cost_usd_month: float
    created_at: datetime
    updated_at: datetime
