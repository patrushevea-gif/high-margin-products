"""LangGraph pipeline — replaces hardcoded sequential worker tasks."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from langgraph.graph import StateGraph, END

from agents.graph_state import PipelineState
from agents.base import AgentContext
from agents.scout import ScoutAgent
from agents.curator import CuratorAgent
from agents.tech_analyst import TechAnalystAgent
from agents.market_analyst import MarketAnalystAgent
from agents.economist import EconomistAgent
from agents.compliance_officer import ComplianceOfficerAgent
from agents.synthesizer import SynthesizerAgent
from agents.devils_advocate import DevilsAdvocateAgent

logger = logging.getLogger(__name__)

DA_REJECT_THRESHOLD = 8.0  # challenge_score >= this → parked, not committee_ready


def _ctx(state: PipelineState, extra: dict[str, Any] | None = None) -> AgentContext:
    return AgentContext(
        hypothesis_id=state.get("hypothesis_id", ""),
        domain=state.get("domain", "lkm"),
        run_id=state.get("run_id"),
        auto_confirm=state.get("auto_confirm", False),
        war_room=state.get("war_room", False),
        extra=extra or {},
    )


def _cost(output: dict[str, Any]) -> float:
    return float((output.get("_usage") or {}).get("cost_usd", 0))


def _make_nodes(gateway: Any) -> dict[str, Any]:
    """Instantiate all agents sharing one gateway."""
    return {
        "scout": ScoutAgent(gateway=gateway),
        "curator": CuratorAgent(gateway=gateway),
        "tech": TechAnalystAgent(gateway=gateway),
        "market": MarketAnalystAgent(gateway=gateway),
        "economist": EconomistAgent(gateway=gateway),
        "compliance": ComplianceOfficerAgent(gateway=gateway),
        "synthesizer": SynthesizerAgent(gateway=gateway),
        "da": DevilsAdvocateAgent(gateway=gateway),
    }


def build_pipeline(gateway: Any) -> Any:
    """Build and compile the LangGraph pipeline. Returns a compiled graph."""
    agents = _make_nodes(gateway)
    graph = StateGraph(PipelineState)

    # ── Node: scout ────────────────────────────────────────────────────────
    async def node_scout(state: PipelineState) -> PipelineState:
        result = await agents["scout"].run(_ctx(state, {"domain": state.get("domain")}))
        out = result.output or {}
        return {**state, "scout_output": out,
                "total_cost_usd": state.get("total_cost_usd", 0) + _cost(out),
                "errors": state.get("errors", []) + ([result.error] if result.error else [])}

    # ── Node: curator ──────────────────────────────────────────────────────
    async def node_curator(state: PipelineState) -> PipelineState:
        result = await agents["curator"].run(
            _ctx(state, {"signals": state.get("scout_output", {}),
                         "hypothesis": state.get("hypothesis", {})}))
        out = result.output or {}
        reject = out.get("reject", False)
        return {**state, "curator_output": out, "early_reject": reject,
                "early_reject_reason": out.get("reject_reason", ""),
                "total_cost_usd": state.get("total_cost_usd", 0) + _cost(out),
                "errors": state.get("errors", []) + ([result.error] if result.error else [])}

    # ── Node: parallel evaluation (tech + market + economics + compliance) ─
    async def node_evaluate(state: PipelineState) -> PipelineState:
        h = state.get("hypothesis", {})
        tasks = [
            agents["tech"].run(_ctx(state, {"hypothesis": h})),
            agents["market"].run(_ctx(state, {"hypothesis": h})),
            agents["economist"].run(_ctx(state, {"hypothesis": h})),
            agents["compliance"].run(_ctx(state, {"hypothesis": h})),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        tech_r, mkt_r, eco_r, cmp_r = results

        def _out(r: Any) -> dict[str, Any]:
            return r.output if hasattr(r, "output") else {}

        added_cost = sum(_cost(_out(r)) for r in results if not isinstance(r, Exception))
        errs = [str(r) for r in results if isinstance(r, Exception)]

        return {**state,
                "tech_output": _out(tech_r),
                "market_output": _out(mkt_r),
                "economics_output": _out(eco_r),
                "compliance_output": _out(cmp_r),
                "total_cost_usd": state.get("total_cost_usd", 0) + added_cost,
                "errors": state.get("errors", []) + errs}

    # ── Node: synthesizer ──────────────────────────────────────────────────
    async def node_synthesizer(state: PipelineState) -> PipelineState:
        evals = {
            "tech": state.get("tech_output", {}),
            "market": state.get("market_output", {}),
            "economics": state.get("economics_output", {}),
            "compliance": state.get("compliance_output", {}),
        }
        result = await agents["synthesizer"].run(
            _ctx(state, {"hypothesis": state.get("hypothesis", {}), "evaluations": evals}))
        out = result.output or {}
        return {**state, "synthesis_output": out,
                "synthesis_committee_ready": bool(out.get("committee_ready", False)),
                "final_score": out.get("overall_score"),
                "final_confidence": out.get("confidence_score"),
                "total_cost_usd": state.get("total_cost_usd", 0) + _cost(out),
                "errors": state.get("errors", []) + ([result.error] if result.error else [])}

    # ── Node: devil's advocate ─────────────────────────────────────────────
    async def node_da(state: PipelineState) -> PipelineState:
        result = await agents["da"].run(
            _ctx(state, {"hypothesis": state.get("hypothesis", {}),
                         "synthesis": state.get("synthesis_output", {})}))
        out = result.output or {}
        score = float(out.get("overall_challenge_score", 0))
        status = "parked" if score >= DA_REJECT_THRESHOLD else "committee_ready"
        return {**state, "da_output": out, "da_challenge_score": score,
                "final_status": status,
                "total_cost_usd": state.get("total_cost_usd", 0) + _cost(out),
                "errors": state.get("errors", []) + ([result.error] if result.error else [])}

    # ── Terminal nodes ─────────────────────────────────────────────────────
    async def node_reject(state: PipelineState) -> PipelineState:
        return {**state, "final_status": "rejected"}

    # ── Register nodes ─────────────────────────────────────────────────────
    graph.add_node("scout", node_scout)
    graph.add_node("curator", node_curator)
    graph.add_node("evaluate", node_evaluate)
    graph.add_node("synthesizer", node_synthesizer)
    graph.add_node("da", node_da)
    graph.add_node("reject", node_reject)

    # ── Edges ──────────────────────────────────────────────────────────────
    graph.set_entry_point("scout")
    graph.add_edge("scout", "curator")

    graph.add_conditional_edges(
        "curator",
        lambda s: "reject" if s.get("early_reject") else "evaluate",
        {"reject": "reject", "evaluate": "evaluate"},
    )

    graph.add_edge("evaluate", "synthesizer")

    graph.add_conditional_edges(
        "synthesizer",
        lambda s: "da" if s.get("synthesis_committee_ready") else "reject",
        {"da": "da", "reject": "reject"},
    )

    graph.add_edge("da", END)
    graph.add_edge("reject", END)

    return graph.compile()
