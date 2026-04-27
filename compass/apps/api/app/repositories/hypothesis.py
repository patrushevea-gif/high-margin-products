from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.hypothesis import Hypothesis
from app.schemas.hypothesis import HypothesisCreate, HypothesisUpdate, HypothesisRead
from app.repositories.base import BaseRepository


class HypothesisRepository(BaseRepository[Hypothesis]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Hypothesis)

    async def list(
        self,
        domain: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[HypothesisRead]:
        q = select(Hypothesis)
        if domain:
            q = q.where(Hypothesis.domain == domain)
        if status:
            q = q.where(Hypothesis.status == status)
        q = q.order_by(Hypothesis.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(q)
        rows = result.scalars().all()
        return [HypothesisRead.model_validate(r) for r in rows]

    async def create(self, data: HypothesisCreate) -> HypothesisRead:
        h = Hypothesis(**data.model_dump())
        await self.save(h)
        return HypothesisRead.model_validate(h)

    async def update(self, id: UUID, data: HypothesisUpdate) -> HypothesisRead:
        h = await self.get_or_404(id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(h, field, value)
        await self.save(h)
        return HypothesisRead.model_validate(h)
