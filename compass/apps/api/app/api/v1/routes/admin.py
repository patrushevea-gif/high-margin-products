from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db

router = APIRouter()


@router.get("/stats")
async def system_stats(db: AsyncSession = Depends(get_db)) -> dict:
    r = await db.execute(text("""
        SELECT
            (SELECT COUNT(*) FROM hypotheses) as hypotheses_total,
            (SELECT COUNT(*) FROM hypotheses WHERE status NOT IN ('rejected','parked')) as hypotheses_active,
            (SELECT COUNT(*) FROM hypotheses WHERE status = 'committee_ready') as committee_ready,
            (SELECT COUNT(*) FROM signals) as signals_total,
            (SELECT COUNT(*) FROM agent_runs WHERE started_at >= now() - interval '24 hours') as runs_today,
            (SELECT COALESCE(SUM(cost_usd), 0) FROM agent_runs WHERE started_at >= now() - interval '24 hours') as cost_today_usd,
            (SELECT COALESCE(SUM(cost_usd), 0) FROM agent_runs WHERE started_at >= now() - interval '30 days') as cost_month_usd,
            (SELECT COUNT(*) FROM sources WHERE is_active = true) as sources_active
    """))
    row = r.mappings().first()
    return dict(row) if row else {}


@router.get("/stats/funnel")
async def funnel_stats(db: AsyncSession = Depends(get_db)) -> list[dict]:
    r = await db.execute(text("""
        SELECT status, COUNT(*) as count
        FROM hypotheses
        GROUP BY status
        ORDER BY count DESC
    """))
    return [dict(row) for row in r.mappings().all()]


@router.get("/stats/signals-daily")
async def signals_daily(db: AsyncSession = Depends(get_db)) -> list[dict]:
    """Last 30 days: signals per day."""
    r = await db.execute(text("""
        SELECT
            DATE(created_at) as day,
            COUNT(*) as signals_count,
            AVG(relevance_score) as avg_relevance
        FROM signals
        WHERE created_at >= now() - interval '30 days'
        GROUP BY DATE(created_at)
        ORDER BY day DESC
    """))
    return [dict(row) for row in r.mappings().all()]
