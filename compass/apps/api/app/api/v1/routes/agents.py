from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.core.database import get_db
from app.schemas.agent import AgentSettingsRead, AgentSettingsUpdate
from app.repositories.agent import AgentSettingsRepository
from app.models.agent import AgentRun

router = APIRouter()


@router.get("/settings", response_model=list[AgentSettingsRead])
async def list_agent_settings(db: AsyncSession = Depends(get_db)) -> list[AgentSettingsRead]:
    repo = AgentSettingsRepository(db)
    return await repo.list()


@router.get("/settings/{agent_name}", response_model=AgentSettingsRead)
async def get_agent_settings(agent_name: str, db: AsyncSession = Depends(get_db)) -> AgentSettingsRead:
    repo = AgentSettingsRepository(db)
    return await repo.get_or_404(agent_name)


@router.patch("/settings/{agent_name}", response_model=AgentSettingsRead)
async def update_agent_settings(
    agent_name: str, body: AgentSettingsUpdate, db: AsyncSession = Depends(get_db)
) -> AgentSettingsRead:
    repo = AgentSettingsRepository(db)
    return await repo.update(agent_name, body)


@router.get("/runs")
async def list_agent_runs(
    hypothesis_id: UUID | None = None,
    agent_name: str | None = None,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    q = select(
        AgentRun.id, AgentRun.agent_name, AgentRun.hypothesis_id,
        AgentRun.status, AgentRun.started_at, AgentRun.finished_at,
        AgentRun.tokens_input, AgentRun.tokens_output, AgentRun.cost_usd,
        AgentRun.error,
    ).order_by(AgentRun.started_at.desc()).limit(limit)

    if hypothesis_id:
        q = q.where(AgentRun.hypothesis_id == hypothesis_id)
    if agent_name:
        q = q.where(AgentRun.agent_name == agent_name)

    result = await db.execute(q)
    rows = result.mappings().all()
    return [dict(r) for r in rows]


@router.get("/stats/daily")
async def agent_daily_stats(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(text("""
        SELECT
            agent_name,
            COUNT(*) as runs,
            SUM(tokens_input + tokens_output) as total_tokens,
            SUM(cost_usd) as total_cost_usd,
            AVG(EXTRACT(EPOCH FROM (finished_at - started_at))) as avg_duration_sec
        FROM agent_runs
        WHERE started_at >= now() - interval '24 hours'
        GROUP BY agent_name
        ORDER BY total_cost_usd DESC
    """))
    rows = result.mappings().all()
    return {"agents": [dict(r) for r in rows]}
