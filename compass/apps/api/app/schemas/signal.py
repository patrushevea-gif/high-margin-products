from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class SignalRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    source_id: UUID | None
    hypothesis_id: UUID | None
    domain: str
    title: str
    summary: str
    url: str | None
    source_type: str
    relevance_score: float
    relevance_rationale: str | None
    is_processed: bool
    is_duplicate: bool
    created_at: datetime
    updated_at: datetime
