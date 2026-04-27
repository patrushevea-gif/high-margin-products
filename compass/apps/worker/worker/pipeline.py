"""Full 8-step hypothesis pipeline.

Scout → Curator → [TechAnalyst ‖ MarketAnalyst ‖ Economist ‖ ComplianceOfficer]
 → Synthesizer → DevilsAdvocate → committee_ready
"""
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


# ─── Helpers ────────────────────────────────────────────────────────────────

async def _get_agent_settings(db: Any, agent_name: str) -> dict:
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT model, temperature, max_tokens, system_prompt, allowed_tools, auto_confirm "
             "FROM agent_settings WHERE agent_name = :n"),
        {"n": agent_name},
    )
    row = result.mappings().first()
    return dict(row) if row else {}


async def _save_run(db: Any, result: Any) -> None:
    from sqlalchemy import text
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
            "output_snapshot": json.dumps(result.output),
            "reasoning_chain": json.dumps(result.reasoning_chain),
            "tokens_input": result.tokens_input,
            "tokens_output": result.tokens_output,
            "cost_usd": result.cost_usd,
            "error": result.error,
        },
    )
    await db.commit()


async def _save_signals(db: Any, signals: list[dict], domain: str, source_id: str | None) -> None:
    from sqlalchemy import text
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


async def _save_evaluation(
    db: Any, hypothesis_id: str, agent_name: str, run_id: str, snapshot: dict
) -> None:
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


async def _get_hypothesis(db: Any, hypothesis_id: str) -> dict:
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT * FROM hypotheses WHERE id = :id"),
        {"id": hypothesis_id},
    )
    row = result.mappings().first()
    return dict(row) if row else {}


async def _set_status(db: Any, hypothesis_id: str, status: str) -> None:
    from sqlalchemy import text
    await db.execute(
        text("UPDATE hypotheses SET status = :status, updated_at = now() WHERE id = :id"),
        {"status": status, "id": hypothesis_id},
    )
    await db.commit()


async def _patch_hypothesis(db: Any, hypothesis_id: str, fields: dict) -> None:
    from sqlalchemy import text
    for col, val in fields.items():
        await db.execute(
            text(f"UPDATE hypotheses SET {col} = :val::jsonb, updated_at = now() WHERE id = :id"),
            {"val": json.dumps(val), "id": hypothesis_id},
        )
    await db.commit()


async def _get_latest_evaluation(db: Any, hypothesis_id: str, agent_name: str) -> dict:
    from sqlalchemy import text
    result = await db.execute(
        text("""SELECT snapshot FROM hypothesis_evaluations
             WHERE hypothesis_id = :hid AND agent_name = :agent
             ORDER BY evaluated_at DESC LIMIT 1"""),
        {"hid": hypothesis_id, "agent": agent_name},
    )
    row = result.mappings().first()
    if not row:
        return {}
    snap = row["snapshot"]
    return json.loads(snap) if isinstance(snap, str) else (snap or {})


# ─── Task definitions ────────────────────────────────────────────────────────

async def task_scout_run(ctx: dict, domain: str = "lkm", source_id: str | None = None) -> dict:
    from agents.scout import ScoutAgent
    from agents.base import AgentContext

    gateway = ctx["ai_gateway"]
    db = ctx["db"]
    settings = await _get_agent_settings(db, "scout")

    agent = ScoutAgent(gateway=gateway, settings=settings)
    result = await agent.run(AgentContext(domain=domain, source_id=source_id))
    await _save_run(db, result)

    signals = result.output.get("signals", [])
    if signals:
        await _save_signals(db, signals, domain, source_id)

    logger.info("Scout: %d signals for domain=%s", len(signals), domain)
    return {"signals": signals, "run_id": result.run_id, "domain": domain}


async def task_curator_run(ctx: dict, signals: list[dict], domain: str = "lkm") -> dict:
    from agents.curator import CuratorAgent
    from agents.base import AgentContext

    gateway = ctx["ai_gateway"]
    db = ctx["db"]
    settings = await _get_agent_settings(db, "curator")

    agent = CuratorAgent(gateway=gateway, settings=settings)
    result = await agent.run(AgentContext(domain=domain, extra={"signals": signals}))
    await _save_run(db, result)

    hypotheses_data = result.output.get("hypotheses", [])
    created_ids: list[str] = []
    from sqlalchemy import text

    for h in hypotheses_data:
        hid = str(uuid.uuid4())
        await db.execute(
            text("""
                INSERT INTO hypotheses (id, title, short_description, domain, status,
                    confidence_score, source_signals, related_hypotheses,
                    resurrection_triggers, tags, created_at, updated_at)
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
        created_ids.append(hid)
    await db.commit()

    logger.info("Curator: created %d hypotheses", len(created_ids))
    return {"hypothesis_ids": created_ids}


async def task_evaluate_tech(ctx: dict, hypothesis_id: str, domain: str = "lkm") -> dict:
    from agents.tech_analyst import TechAnalystAgent
    from agents.base import AgentContext

    gateway = ctx["ai_gateway"]
    db = ctx["db"]
    settings = await _get_agent_settings(db, "tech_analyst")
    hypothesis = await _get_hypothesis(db, hypothesis_id)

    agent = TechAnalystAgent(gateway=gateway, settings=settings)
    result = await agent.run(AgentContext(
        hypothesis_id=hypothesis_id, domain=domain, extra={"hypothesis": hypothesis}
    ))
    await _save_run(db, result)
    await _save_evaluation(db, hypothesis_id, "tech_analyst", result.run_id, result.output)

    if result.output:
        await _patch_hypothesis(db, hypothesis_id, {"technical": result.output})
    await _set_status(db, hypothesis_id, "tech_evaluated")
    return {"hypothesis_id": hypothesis_id, "verdict": result.output.get("verdict")}


async def task_evaluate_market(ctx: dict, hypothesis_id: str, domain: str = "lkm") -> dict:
    from agents.market_analyst import MarketAnalystAgent
    from agents.base import AgentContext

    gateway = ctx["ai_gateway"]
    db = ctx["db"]
    settings = await _get_agent_settings(db, "market_analyst")
    hypothesis = await _get_hypothesis(db, hypothesis_id)

    agent = MarketAnalystAgent(gateway=gateway, settings=settings)
    result = await agent.run(AgentContext(
        hypothesis_id=hypothesis_id, domain=domain, extra={"hypothesis": hypothesis}
    ))
    await _save_run(db, result)
    await _save_evaluation(db, hypothesis_id, "market_analyst", result.run_id, result.output)

    if result.output:
        await _patch_hypothesis(db, hypothesis_id, {"market": result.output})
    await _set_status(db, hypothesis_id, "market_evaluated")
    return {"hypothesis_id": hypothesis_id, "verdict": result.output.get("market_verdict")}


async def task_evaluate_economics(ctx: dict, hypothesis_id: str, domain: str = "lkm") -> dict:
    from agents.economist import EconomistAgent
    from agents.base import AgentContext

    gateway = ctx["ai_gateway"]
    db = ctx["db"]
    settings = await _get_agent_settings(db, "economist")
    hypothesis = await _get_hypothesis(db, hypothesis_id)
    market_data = await _get_latest_evaluation(db, hypothesis_id, "market_analyst")

    agent = EconomistAgent(gateway=gateway, settings=settings)
    result = await agent.run(AgentContext(
        hypothesis_id=hypothesis_id, domain=domain,
        extra={"hypothesis": hypothesis, "market_evaluation": market_data},
    ))
    await _save_run(db, result)
    await _save_evaluation(db, hypothesis_id, "economist", result.run_id, result.output)

    if result.output:
        await _patch_hypothesis(db, hypothesis_id, {"economics": result.output})
    await _set_status(db, hypothesis_id, "economics_evaluated")

    # Update confidence score based on economic verdict
    verdict = result.output.get("economic_verdict", "unknown")
    conf = {"viable": 0.7, "marginal": 0.4, "not_viable": 0.1}.get(verdict, 0.3)
    from sqlalchemy import text
    await db.execute(
        text("UPDATE hypotheses SET confidence_score = :c, updated_at = now() WHERE id = :id"),
        {"c": conf, "id": hypothesis_id},
    )
    await db.commit()
    return {"hypothesis_id": hypothesis_id, "verdict": verdict}


async def task_evaluate_compliance(ctx: dict, hypothesis_id: str, domain: str = "lkm") -> dict:
    from agents.compliance_officer import ComplianceOfficerAgent
    from agents.base import AgentContext

    gateway = ctx["ai_gateway"]
    db = ctx["db"]
    settings = await _get_agent_settings(db, "compliance_officer")
    hypothesis = await _get_hypothesis(db, hypothesis_id)

    agent = ComplianceOfficerAgent(gateway=gateway, settings=settings)
    result = await agent.run(AgentContext(
        hypothesis_id=hypothesis_id, domain=domain, extra={"hypothesis": hypothesis}
    ))
    await _save_run(db, result)
    await _save_evaluation(db, hypothesis_id, "compliance_officer", result.run_id, result.output)

    if result.output:
        await _patch_hypothesis(db, hypothesis_id, {"risks": result.output})
    await _set_status(db, hypothesis_id, "compliance_checked")
    return {"hypothesis_id": hypothesis_id, "verdict": result.output.get("overall_compliance_verdict")}


async def task_synthesize(ctx: dict, hypothesis_id: str, domain: str = "lkm") -> dict:
    from agents.synthesizer import SynthesizerAgent
    from agents.base import AgentContext

    gateway = ctx["ai_gateway"]
    db = ctx["db"]
    settings = await _get_agent_settings(db, "synthesizer")
    hypothesis = await _get_hypothesis(db, hypothesis_id)

    evaluations = {
        "tech": await _get_latest_evaluation(db, hypothesis_id, "tech_analyst"),
        "market": await _get_latest_evaluation(db, hypothesis_id, "market_analyst"),
        "economics": await _get_latest_evaluation(db, hypothesis_id, "economist"),
        "compliance": await _get_latest_evaluation(db, hypothesis_id, "compliance_officer"),
    }

    agent = SynthesizerAgent(gateway=gateway, settings=settings)
    result = await agent.run(AgentContext(
        hypothesis_id=hypothesis_id, domain=domain,
        extra={"hypothesis": hypothesis, "evaluations": evaluations},
    ))
    await _save_run(db, result)
    await _save_evaluation(db, hypothesis_id, "synthesizer", result.run_id, result.output)

    from sqlalchemy import text
    score = result.output.get("overall_score")
    if score is not None:
        await db.execute(
            text("UPDATE hypotheses SET overall_score = :s, last_evaluated_at = now(), updated_at = now() WHERE id = :id"),
            {"s": float(score), "id": hypothesis_id},
        )
        await db.commit()

    await _set_status(db, hypothesis_id, "synthesized")
    return {"hypothesis_id": hypothesis_id, "committee_ready": result.output.get("committee_ready", False)}


async def task_devils_advocate(ctx: dict, hypothesis_id: str, domain: str = "lkm") -> dict:
    from agents.devils_advocate import DevilsAdvocateAgent
    from agents.base import AgentContext

    gateway = ctx["ai_gateway"]
    db = ctx["db"]
    settings = await _get_agent_settings(db, "devils_advocate")
    hypothesis = await _get_hypothesis(db, hypothesis_id)

    evaluations = {
        "tech": await _get_latest_evaluation(db, hypothesis_id, "tech_analyst"),
        "market": await _get_latest_evaluation(db, hypothesis_id, "market_analyst"),
        "economics": await _get_latest_evaluation(db, hypothesis_id, "economist"),
        "compliance": await _get_latest_evaluation(db, hypothesis_id, "compliance_officer"),
        "synthesis": await _get_latest_evaluation(db, hypothesis_id, "synthesizer"),
    }

    agent = DevilsAdvocateAgent(gateway=gateway, settings=settings)
    result = await agent.run(AgentContext(
        hypothesis_id=hypothesis_id, domain=domain,
        extra={"hypothesis": hypothesis, "evaluations": evaluations},
    ))
    await _save_run(db, result)
    await _save_evaluation(db, hypothesis_id, "devils_advocate", result.run_id, result.output)
    await _set_status(db, hypothesis_id, "challenged")
    return {
        "hypothesis_id": hypothesis_id,
        "should_proceed": result.output.get("should_proceed_despite_risks", True),
        "challenge_score": result.output.get("overall_challenge_score", 5),
    }


async def task_run_full_pipeline(ctx: dict, hypothesis_id: str, domain: str = "lkm") -> dict:
    """Run all evaluation stages for one hypothesis end-to-end."""
    logger.info("Full pipeline start for hypothesis_id=%s", hypothesis_id)

    tech = await task_evaluate_tech(ctx, hypothesis_id, domain)
    market = await task_evaluate_market(ctx, hypothesis_id, domain)
    econ = await task_evaluate_economics(ctx, hypothesis_id, domain)
    compliance = await task_evaluate_compliance(ctx, hypothesis_id, domain)
    synthesis = await task_synthesize(ctx, hypothesis_id, domain)
    da = await task_devils_advocate(ctx, hypothesis_id, domain)

    # Promote to committee_ready if synthesis says so and DA doesn't flag fatal
    if synthesis.get("committee_ready") and da.get("challenge_score", 10) < 8:
        from sqlalchemy import text
        await ctx["db"].execute(
            text("UPDATE hypotheses SET status = 'committee_ready', updated_at = now() WHERE id = :id"),
            {"id": hypothesis_id},
        )
        await ctx["db"].commit()
        final_status = "committee_ready"
    else:
        final_status = "synthesized"

    logger.info("Full pipeline done for %s → status=%s", hypothesis_id, final_status)
    return {"hypothesis_id": hypothesis_id, "final_status": final_status}


async def task_scout_and_process(ctx: dict, domain: str = "lkm") -> dict:
    """Full cycle: scout → curator → launch pipelines for new hypotheses."""
    scout_result = await task_scout_run(ctx, domain=domain)
    signals = scout_result.get("signals", [])

    if not signals:
        return {"hypotheses_created": 0}

    curator_result = await task_curator_run(ctx, signals=signals, domain=domain)
    hypothesis_ids = curator_result.get("hypothesis_ids", [])

    # Launch pipeline for each new hypothesis (up to 5 per run to control cost)
    for hid in hypothesis_ids[:5]:
        await task_run_full_pipeline(ctx, hypothesis_id=hid, domain=domain)

    return {"hypotheses_created": len(hypothesis_ids), "pipelines_run": min(len(hypothesis_ids), 5)}
