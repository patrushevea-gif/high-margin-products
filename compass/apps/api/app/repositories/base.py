from uuid import UUID
from typing import TypeVar, Generic, Type
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, db: AsyncSession, model: Type[ModelT]) -> None:
        self.db = db
        self.model = model

    async def get(self, id: UUID) -> ModelT | None:
        result = await self.db.execute(select(self.model).where(self.model.id == id))  # type: ignore
        return result.scalar_one_or_none()

    async def get_or_404(self, id: UUID) -> ModelT:
        obj = await self.get(id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} {id} not found",
            )
        return obj

    async def save(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id: UUID) -> None:
        obj = await self.get_or_404(id)
        await self.db.delete(obj)
        await self.db.commit()
