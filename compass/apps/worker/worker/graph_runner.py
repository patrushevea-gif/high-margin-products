"""Run the LangGraph pipeline for a single hypothesis."""
from __future__ import annotations

import sys
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Any

sys.path.insert(0, "/packages/agents")
sys.path.insert(0, "/packages/tools")

logger = logging.getLogger(__name__)

_AGENT_OUTPUT_KEYS = {
    "tech": "tech_output",
    "market": "market_output",
    "economics": "economics_output",
    "compliance": "compliance_output",
    "synthesis": "synthesis_output",
    "da": "da_output",
}


async def _get_hypothesis(db: Any, hypothesis_id: str) -> dict:
    from sqlalchemy import text
    r = await db.execute(
        text("SELECT * FROM hypotheses WHERE id = :id"),
        {"id": hypothesis_id},
    )
    row = r.mappings().first()
    return dict(row) if row else {}


async def _set_status(db: Any, hypothesis_id: str, status: str,
                      score: float | None, confidence: float | None) -> None:
    from sqlalchemy import text
    await db.execute(
        text("""UPDATE hypotheses SET status=:s, overall_score=COALESCE(:sc, overall_score),
                confidence_score=COALESCE(:c, confidence_score), updated_at=now()
                WHERE id=:id"""),
        {"s": status, "sc": score, "c": confidence, "id": hypothesis_id},
    )
    await db.commit()


async def _save_evaluation(db: Any, hypothesis_id: str, agent_name: str,
                           run_id: str, snapshot: dict) -> None:
    from sqlalchemy import text
    await db.execute(
        text("""INSERT INTO hypothesis_evaluations
                (id, hypothesis_id, agent_name, run_id, evaluated_at, snapshot, created_at, updated_at)
                VALUES (:id, :hid, :agent, :run_id, now(), :snap::jsonb, now(), now())"""),
        {"id": str(uuid.uuid4()), "hid": hypothesis_id, "agent": agent_name,
         "run_id": run_id, "snap": json.dumps(snapshot, default=str)},
    )
    await db.commit()


async def run_graph_pipeline(ctx: Any, hypothesis_id: str) -> dict[str, Any]:
    """
    Entry point called by the arq worker task.
    Builds the LangGraph, runs it, persists results to DB.
    """
    from agents.pipeline_graph import build_pipeline
    from app.core.database import AsyncSessionLocal
    from app.services.ai_gateway import AIGateway

    run_id = str(uuid.uuid4())
    logger.info("graph_pipeline start hypothesis=%s run=%s", hypothesis_id, run_id)

    gateway = AIGateway()

    async with AsyncSessionLocal() as db:
        hypothesis = await _get_hypothesis(db, hypothesis_id)
        if not hypothesis:
            logger.error("hypothesis %s not found", hypothesis_id)
            return {"status": "error", "reason": "not_found"}

        domain = str(hypothesis.get("domain", "lkm"))

    # Build and run the compiled graph
    pipeline = build_pipeline(gateway)
    initial_state = {
        "hypothesis_id": hypothesis_id,
        "domain": domain,
        "run_id": run_id,
        "hypothesis": {k: (v.isoformat() if hasattr(v, "isoformat") else v)
                       for k, v in hypothesis.items()},
        "total_cost_usd": 0.0,
        "errors": [],
    }

    try:
        final_state = await pipeline.ainvoke(initial_state)
    except Exception as exc:
        logger.exception("graph pipeline failed: %s", exc)
        return {"status": "error", "reason": str(exc)}

    # Persist final status and scores
    async with AsyncSessionLocal() as db:
        await _set_status(
            db, hypothesis_id,
            final_state.get("final_status", "parked"),
            final_state.get("final_score"),
            final_state.get("final_confidence"),
        )

        # Save Time Machine snapshots for each agent that produced output
        for agent_name, state_key in _AGENT_OUTPUT_KEYS.items():
            snapshot = final_state.get(state_key)
            if snapshot:
                await _save_evaluation(db, hypothesis_id, agent_name, run_id, snapshot)

    total_cost = final_state.get("total_cost_usd", 0)
    logger.info("graph_pipeline done hypothesis=%s status=%s cost=$%.4f",
                hypothesis_id, final_state.get("final_status"), total_cost)

    return {
        "hypothesis_id": hypothesis_id,
        "run_id": run_id,
        "final_status": final_state.get("final_status"),
        "final_score": final_state.get("final_score"),
        "total_cost_usd": total_cost,
        "errors": final_state.get("errors", []),
    }
