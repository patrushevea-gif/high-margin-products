"""LangGraph state definition for the Compass agent pipeline."""
from __future__ import annotations

from typing import Any
from typing_extensions import TypedDict


class PipelineState(TypedDict, total=False):
    # ── Input ──────────────────────────────────────────────────────────────
    hypothesis_id: str
    domain: str
    run_id: str
    auto_confirm: bool
    war_room: bool

    # Raw hypothesis record fetched from DB at graph entry
    hypothesis: dict[str, Any]

    # ── Agent outputs ──────────────────────────────────────────────────────
    scout_output: dict[str, Any]
    curator_output: dict[str, Any]
    tech_output: dict[str, Any]
    market_output: dict[str, Any]
    economics_output: dict[str, Any]
    compliance_output: dict[str, Any]
    synthesis_output: dict[str, Any]
    da_output: dict[str, Any]          # DevilsAdvocate

    # ── Routing flags ──────────────────────────────────────────────────────
    # Set by curator node when a hypothesis should be rejected early
    early_reject: bool
    early_reject_reason: str

    # Set by synthesizer: whether DA should proceed
    synthesis_committee_ready: bool

    # Set by DA: numeric challenge score (0-10)
    da_challenge_score: float

    # ── Final verdict ──────────────────────────────────────────────────────
    # "committee_ready" | "rejected" | "parked" | "error"
    final_status: str
    final_score: float | None
    final_confidence: float | None

    # Accumulated cost across all agents
    total_cost_usd: float

    # List of error strings from any node that raised
    errors: list[str]
