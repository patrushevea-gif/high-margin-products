from __future__ import annotations
from uuid import UUID
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


DomainType = Literal[
    "lkm", "soj", "lubricants", "anticor", "sealants",
    "adhesives", "specialty", "reagents", "additives", "surfactants"
]

HypothesisStatus = Literal[
    "draft", "signal_processed", "tech_evaluated", "market_evaluated",
    "economics_evaluated", "compliance_checked", "synthesized",
    "challenged", "committee_ready", "committee_decision",
    "accepted", "rejected", "parked", "to_review"
]


class TechnicalProfile(BaseModel):
    complexity: int | None = Field(None, ge=1, le=5, description="1=simple, 5=very complex")
    equipment_modification: Literal["none", "minor", "major", "new"] | None = None
    raw_material_availability: Literal["available", "partial", "closed"] | None = None
    trl: int | None = Field(None, ge=1, le=9, description="Technology Readiness Level")
    notes: str | None = None


class MarketProfile(BaseModel):
    market_size_mln_rub: float | None = None
    cagr_pct: float | None = None
    competitive_density: Literal["low", "medium", "high"] | None = None
    target_segments: list[str] = []
    geographic_focus: list[str] = []
    notes: str | None = None


class EconomicsProfile(BaseModel):
    cost_per_unit_rub: float | None = None
    price_per_unit_rub: float | None = None
    margin_pct: float | None = None
    margin_rub_per_unit: float | None = None
    min_batch_units: int | None = None
    roi_months: int | None = None
    notes: str | None = None


class RisksProfile(BaseModel):
    overall_risk_score: float | None = Field(None, ge=1, le=10)
    patent_risk: float | None = Field(None, ge=0, le=1)
    regulatory_risk: float | None = Field(None, ge=0, le=1)
    raw_material_volatility_risk: float | None = Field(None, ge=0, le=1)
    technology_risk: float | None = Field(None, ge=0, le=1)
    notes: str | None = None


class ResurrectionTrigger(BaseModel):
    type: Literal["price_change", "patent_expiry", "regulation_change", "other"]
    target: str | None = None
    operator: str | None = None
    value: float | None = None
    unit: str | None = None
    description: str | None = None


# ─── API schemas ────────────────────────────────────────────────────────────

class HypothesisCreate(BaseModel):
    title: str = Field(..., max_length=500)
    short_description: str
    long_description: str | None = None
    domain: DomainType = "lkm"
    curator_id: UUID | None = None
    tags: list[str] = []


class HypothesisUpdate(BaseModel):
    title: str | None = None
    short_description: str | None = None
    long_description: str | None = None
    status: HypothesisStatus | None = None
    curator_id: UUID | None = None
    technical: TechnicalProfile | None = None
    market: MarketProfile | None = None
    economics: EconomicsProfile | None = None
    risks: RisksProfile | None = None
    war_room_active: bool | None = None
    tags: list[str] | None = None


class HypothesisRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    organization_id: UUID | None = None
    created_by: str | None = None
    title: str
    short_description: str
    long_description: str | None
    domain: str
    status: str
    curator_id: UUID | None
    technical: dict | None
    market: dict | None
    economics: dict | None
    risks: dict | None
    confidence_score: float
    overall_score: float | None
    source_signals: list
    related_hypotheses: list
    resurrection_triggers: list
    war_room_active: bool
    auto_confirm_override: bool | None
    last_evaluated_at: datetime | None
    tags: list
    created_at: datetime
    updated_at: datetime
