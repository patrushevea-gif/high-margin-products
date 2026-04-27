"""Hypothesis pipeline: Scout → Curator → TechAnalyst → Synthesizer.

Each step is an arq task. Orchestrator chains them.
"""
from __future__ import annotations

import sys
import logging
from datetime import datetime, timezone
from typing import Any

sys.path.insert(0, "/packages/agents")
sys.path.insert(0, "/packages/tools")

from arq import ArqRedis

logger = logging.getLogger(__name__)


async def task_scout_run(ctx: dict, domain: str = "lkm", source_id: str | None = None) -> dict:
    """Run Scout agent to collect raw signals."""
    from agents.scout import ScoutAgent
    from agents.base import AgentContext

    gateway = ctx["ai_gateway"]
    db = ctx["db"]
    settings = await _get_agent_settings(db, "scout")

    agent = ScoutAgent(gateway=gateway, settings=settings)
    agent_ctx = AgentContext(domain=domain, source_id=source_id)

    result = await agent.run(agent_ctx)
    await _save_agent_run(db, result)

    if result.status == "completed":
        signals = result.output.get("signals", [])
        await _save_signals(db, signals, domain, source_id)
        logger.info("Scout: saved %d signals for domain=%s", len(signals), domain)
        return {"signals": signals, "run_id": result.run_id}

    return {"signals": [], "run_id": result.run_id, "error": result.error}


async def task_curator_run(ctx: dict, signals: list[dict], domain: str = "lkm") -> dict:
    """Run Curator on a batch of signals → create hypothesis drafts."""
    from agents.curator import CuratorAgent
    from agents.base import AgentContext

    gateway = ctx["ai_gateway"]
    db = ctx["db"]
    settings = await _get_agent_settings(db, "curator")

    agent = CuratorAgent(gateway=gateway, settings=settings)
    agent_ctx = AgentContext(domain=domain, extra={"signals": signals})

    result = await agent.run(agent_ctx)
    await _save_agent_run(db, result)

    hypotheses = result.output.get("hypotheses", [])
    created_ids = await _create_hypothesis_drafts(db, hypotheses, domain)
    logger.info("Curator: created %d hypothesis drafts", len(created_ids))
    return {"hypothesis_ids": created_ids}


async def task_evaluate_hypothesis(ctx: dict, hypothesis_id: str, domain: str = "lkm") -> dict:
    """Run TechAnalyst on a hypothesis."""
    from agents.tech_analyst import TechAnalystAgent
    from agents.base import AgentContext

    gateway = ctx["ai_gateway"]
    db = ctx["db"]
    settings = await _get_agent_settings(db, "tech_analyst")
    hypothesis = await _get_hypothesis(db, hypothesis_id)

    agent = TechAnalystAgent(gateway=gateway, settings=settings)
    agent_ctx = AgentContext(
        hypothesis_id=hypothesis_id,
        domain=domain,
        extra={"hypothesis": hypothesis},
    )

    result = await agent.run(agent_ctx)
    await _save_agent_run(db, result)
    await _save_evaluation(db, hypothesis_id, "tech_analyst", result.run_id, result.output)
    await _update_hypothesis_status(db, hypothesis_id, "tech_evaluated", result.output)

    return {"hypothesis_id": hypothesis_id, "status": "tech_evaluated", "run_id": result.run_id}


async def task_synthesize_hypothesis(ctx: dict, hypothesis_id: str, domain: str = "lkm") -> dict:
    """Run Synthesizer to produce committee-ready conclusion."""
    from agents.synthesizer import SynthesizerAgent
    from agents.base import AgentContext

    gateway = ctx["ai_gateway"]
    db = ctx["db"]
    settings = await _get_agent_settings(db, "synthesizer")
    hypothesis = await _get_hypothesis(db, hypothesis_id)

    agent = SynthesizerAgent(gateway=gateway, settings=settings)
    agent_ctx = AgentContext(
        hypothesis_id=hypothesis_id,
        domain=domain,
        extra={"hypothesis": hypothesis, "evaluations": {}},
    )

    result = await agent.run(agent_ctx)
    await _save_agent_run(db, result)
    await _save_evaluation(db, hypothesis_id, "synthesizer", result.run_id, result.output)

    is_ready = result.output.get("committee_ready", False)
    new_status = "synthesized" if not is_ready else "committee_ready"
    await _update_hypothesis_status(db, hypothesis_id, new_status, result.output)

    return {"hypothesis_id": hypothesis_id, "status": new_status}


# ─── DB helpers ──────────────────────────────────────────────────────────────

async def _get_agent_settings(db: Any, agent_name: str) -> dict:
    from sqlalchemy import select, text
    result = await db.execute(
        text("SELECT model, temperature, max_tokens, system_prompt, allowed_tools FROM agent_settings WHERE agent_name = :n"),
        {"n": agent_name},
    )
    row = result.mappings().first()
    return dict(row) if row else {}


async def _save_agent_run(db: Any, result: Any) -> None:
    from sqlalchemy import text
    import uuid
    await db.execute(
        text("""
            INSERT INTO agent_runs (id, agent_name, hypothesis_id, status,
                started_at, finished_at, output_snapshot, reasoning_chain,
                tokens_input, tokens_output, cost_usd, error, created_at, updated_at)
            VALUES (:id, :agent_name, :hypothesis_id, :status,
                :started_at, :finished_at, :output_snapshot::jsonb, :reasoning_chain::jsonb,
                :tokens_input, :tokens_output, :cost_usd, :error, now(), now())
        """),
        {
            "id": result.run_id,
            "agent_name": result.agent_name,
            "hypothesis_id": result.hypothesis_id,
            "status": result.status,
            "started_at": result.started_at,
            "finished_at": result.finished_at,
            "output_snapshot": str(result.output),
            "reasoning_chain": str(result.reasoning_chain),
            "tokens_input": result.tokens_input,
            "tokens_output": result.tokens_output,
            "cost_usd": result.cost_usd,
            "error": result.error,
        },
    )
    await db.commit()


async def _save_signals(db: Any, signals: list[dict], domain: str, source_id: str | None) -> None:
    import json
    from sqlalchemy import text
    import uuid
    for sig in signals:
        await db.execute(
            text("""
                INSERT INTO signals (id, source_id, domain, title, summary, url,
                    source_type, relevance_score, relevance_rationale, raw_data,
                    is_processed, created_at, updated_at)
                VALUES (:id, :source_id, :domain, :title, :summary, :url,
                    :source_type, :relevance_score, :relevance_rationale, :raw_data::jsonb,
                    false, now(), now())
            """),
            {
                "id": str(uuid.uuid4()),
                "source_id": source_id,
                "domain": domain,
                "title": sig.get("title", "")[:500],
                "summary": sig.get("summary", ""),
                "url": sig.get("url"),
                "source_type": sig.get("source_type", "general"),
                "relevance_score": float(sig.get("relevance_score", 0)),
                "relevance_rationale": sig.get("relevance_rationale"),
                "raw_data": json.dumps(sig),
            },
        )
    await db.commit()


async def _create_hypothesis_drafts(db: Any, hypotheses: list[dict], domain: str) -> list[str]:
    import uuid
    from sqlalchemy import text
    ids = []
    for h in hypotheses:
        hid = str(uuid.uuid4())
        await db.execute(
            text("""
                INSERT INTO hypotheses (id, title, short_description, domain, status,
                    confidence_score, source_signals, related_hypotheses, resurrection_triggers,
                    tags, created_at, updated_at)
                VALUES (:id, :title, :desc, :domain, 'signal_processed',
                    :confidence, '[]'::jsonb, '[]'::jsonb, '[]'::jsonb, '[]'::jsonb, now(), now())
            """),
            {
                "id": hid,
                "title": h.get("title", "")[:500],
                "desc": h.get("short_description", ""),
                "domain": domain,
                "confidence": float(h.get("relevance_score", 0)),
            },
        )
        ids.append(hid)
    await db.commit()
    return ids


async def _get_hypothesis(db: Any, hypothesis_id: str) -> dict:
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT * FROM hypotheses WHERE id = :id"),
        {"id": hypothesis_id},
    )
    row = result.mappings().first()
    return dict(row) if row else {}


async def _save_evaluation(db: Any, hypothesis_id: str, agent_name: str, run_id: str, snapshot: dict) -> None:
    import uuid, json
    from sqlalchemy import text
    await db.execute(
        text("""
            INSERT INTO hypothesis_evaluations (id, hypothesis_id, agent_name, run_id,
                evaluated_at, snapshot, created_at, updated_at)
            VALUES (:id, :hypothesis_id, :agent_name, :run_id,
                now(), :snapshot::jsonb, now(), now())
        """),
        {
            "id": str(uuid.uuid4()),
            "hypothesis_id": hypothesis_id,
            "agent_name": agent_name,
            "run_id": run_id,
            "snapshot": json.dumps(snapshot),
        },
    )
    await db.commit()


async def _update_hypothesis_status(db: Any, hypothesis_id: str, status: str, output: dict) -> None:
    import json
    from sqlalchemy import text
    # Map agent output fields to hypothesis columns
    updates: dict = {"status": status}
    if "complexity" in output:
        updates["technical"] = json.dumps(output)
    if "executive_summary" in output:
        updates["overall_score"] = float(output.get("overall_score", 0))

    await db.execute(
        text("UPDATE hypotheses SET status = :status, updated_at = now() WHERE id = :id"),
        {"status": status, "id": hypothesis_id},
    )
    await db.commit()
