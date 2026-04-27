from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.agent import AgentSettings
from app.schemas.agent import AgentSettingsUpdate, AgentSettingsRead
from app.repositories.base import BaseRepository


class AgentSettingsRepository(BaseRepository[AgentSettings]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, AgentSettings)

    async def list(self) -> list[AgentSettingsRead]:
        q = select(AgentSettings).order_by(AgentSettings.agent_name)
        result = await self.db.execute(q)
        rows = result.scalars().all()
        return [AgentSettingsRead.model_validate(r) for r in rows]

    async def get_or_404(self, agent_name: str) -> AgentSettingsRead:  # type: ignore[override]
        q = select(AgentSettings).where(AgentSettings.agent_name == agent_name)
        result = await self.db.execute(q)
        obj = result.scalar_one_or_none()
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_name} not found")
        return AgentSettingsRead.model_validate(obj)

    async def update(self, agent_name: str, data: AgentSettingsUpdate) -> AgentSettingsRead:
        q = select(AgentSettings).where(AgentSettings.agent_name == agent_name)
        result = await self.db.execute(q)
        obj = result.scalar_one_or_none()
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_name} not found")

        updates = data.model_dump(exclude_none=True)
        if "system_prompt" in updates:
            obj.prompt_history = list(obj.prompt_history or []) + [{
                "version": obj.system_prompt_version,
                "prompt": obj.system_prompt,
            }]
            obj.system_prompt_version += 1

        for field, value in updates.items():
            setattr(obj, field, value)

        await self.save(obj)
        return AgentSettingsRead.model_validate(obj)
