from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.agent import AgentSettingsRead, AgentSettingsUpdate
from app.repositories.agent import AgentSettingsRepository

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


@router.get("/runs", response_model=list[dict])
async def list_agent_runs(
    hypothesis_id: UUID | None = None,
    agent_name: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    return []
