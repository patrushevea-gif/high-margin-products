from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.source import SourceRead, SourceCreate, SourceUpdate
from app.repositories.source import SourceRepository

router = APIRouter()


@router.get("/", response_model=list[SourceRead])
async def list_sources(db: AsyncSession = Depends(get_db)) -> list[SourceRead]:
    repo = SourceRepository(db)
    return await repo.list()


@router.post("/", response_model=SourceRead, status_code=201)
async def create_source(body: SourceCreate, db: AsyncSession = Depends(get_db)) -> SourceRead:
    repo = SourceRepository(db)
    return await repo.create(body)


@router.get("/{source_id}", response_model=SourceRead)
async def get_source(source_id: UUID, db: AsyncSession = Depends(get_db)) -> SourceRead:
    repo = SourceRepository(db)
    return await repo.get_or_404(source_id)


@router.patch("/{source_id}", response_model=SourceRead)
async def update_source(
    source_id: UUID, body: SourceUpdate, db: AsyncSession = Depends(get_db)
) -> SourceRead:
    repo = SourceRepository(db)
    return await repo.update(source_id, body)


@router.post("/{source_id}/trigger")
async def trigger_source(source_id: UUID, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Manually trigger a source scrape run."""
    repo = SourceRepository(db)
    await repo.get_or_404(source_id)
    return {"source_id": str(source_id), "status": "queued"}
