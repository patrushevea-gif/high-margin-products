from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class AgentSettingsUpdate(BaseModel):
    model: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=1.0)
    max_tokens: int | None = Field(None, ge=256, le=32768)
    system_prompt: str | None = None
    allowed_tools: list[str] | None = None
    auto_confirm: bool | None = None
    cost_limit_per_run_usd: float | None = None
    schedule: str | None = None
    is_active: bool | None = None


class AgentSettingsRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    agent_name: str
    display_name: str
    description: str
    model: str
    temperature: float
    max_tokens: int
    system_prompt: str
    system_prompt_version: int
    allowed_tools: list
    auto_confirm: bool
    cost_limit_per_run_usd: float
    schedule: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
