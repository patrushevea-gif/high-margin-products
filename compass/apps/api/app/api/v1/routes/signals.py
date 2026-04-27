from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.signal import SignalRead
from app.repositories.signal import SignalRepository

router = APIRouter()


@router.get("/", response_model=list[SignalRead])
async def list_signals(
    source_id: UUID | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[SignalRead]:
    repo = SignalRepository(db)
    return await repo.list(source_id=source_id, limit=limit, offset=offset)


@router.get("/{signal_id}", response_model=SignalRead)
async def get_signal(signal_id: UUID, db: AsyncSession = Depends(get_db)) -> SignalRead:
    repo = SignalRepository(db)
    return await repo.get_or_404(signal_id)
