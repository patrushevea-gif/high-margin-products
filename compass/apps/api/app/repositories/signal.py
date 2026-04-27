from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.signal import Signal
from app.schemas.signal import SignalRead
from app.repositories.base import BaseRepository


class SignalRepository(BaseRepository[Signal]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Signal)

    async def list(
        self,
        source_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SignalRead]:
        q = select(Signal)
        if source_id:
            q = q.where(Signal.source_id == source_id)
        q = q.order_by(Signal.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(q)
        rows = result.scalars().all()
        return [SignalRead.model_validate(r) for r in rows]
