from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceUpdate, SourceRead
from app.repositories.base import BaseRepository


class SourceRepository(BaseRepository[Source]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Source)

    async def list(self) -> list[SourceRead]:
        q = select(Source).order_by(Source.source_type, Source.name)
        result = await self.db.execute(q)
        rows = result.scalars().all()
        return [SourceRead.model_validate(r) for r in rows]

    async def create(self, data: SourceCreate) -> SourceRead:
        s = Source(**data.model_dump())
        await self.save(s)
        return SourceRead.model_validate(s)

    async def update(self, id: UUID, data: SourceUpdate) -> SourceRead:
        s = await self.get_or_404(id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(s, field, value)
        await self.save(s)
        return SourceRead.model_validate(s)
