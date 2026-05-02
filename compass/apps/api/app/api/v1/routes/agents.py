from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.core.database import get_db
from app.schemas.agent import AgentSettingsRead, AgentSettingsUpdate
from app.repositories.agent import AgentSettingsRepository
from app.models.agent import AgentSettings, AgentRun

router = APIRouter()

# Temperature configs per agent per preset mode
# fmt: off
_PRESETS: dict[str, dict[str, float]] = {
    "conservative": {
        "scout": 0.2, "curator": 0.2, "tech_analyst": 0.2,
        "market_analyst": 0.2, "economist": 0.1, "compliance_officer": 0.1,
        "synthesizer": 0.2, "devils_advocate": 0.5, "orchestrator": 0.1,
    },
    "balanced": {
        "scout": 0.3, "curator": 0.4, "tech_analyst": 0.3,
        "market_analyst": 0.5, "economist": 0.2, "compliance_officer": 0.2,
        "synthesizer": 0.4, "devils_advocate": 0.7, "orchestrator": 0.1,
    },
    "explorer": {
        "scout": 0.6, "curator": 0.5, "tech_analyst": 0.4,
        "market_analyst": 0.6, "economist": 0.3, "compliance_officer": 0.3,
        "synthesizer": 0.5, "devils_advocate": 0.8, "orchestrator": 0.2,
    },
    "maverick": {
        "scout": 0.9, "curator": 0.7, "tech_analyst": 0.6,
        "market_analyst": 0.8, "economist": 0.5, "compliance_officer": 0.4,
        "synthesizer": 0.7, "devils_advocate": 1.0, "orchestrator": 0.3,
    },
}
# fmt: on


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


@router.post("/presets/{mode}")
async def apply_preset(mode: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Apply a thinking-mode preset — bulk-update temperatures for all agents."""
    if mode not in _PRESETS:
        raise HTTPException(status_code=400, detail=f"Unknown preset '{mode}'. Choose: {list(_PRESETS)}")
    temps = _PRESETS[mode]
    updated = []
    for agent_name, temperature in temps.items():
        result = await db.execute(select(AgentSettings).where(AgentSettings.agent_name == agent_name))
        obj = result.scalar_one_or_none()
        if obj:
            obj.temperature = temperature
            await db.flush()
            updated.append(agent_name)
    await db.commit()
    return {"mode": mode, "updated": updated, "temperatures": temps}


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
