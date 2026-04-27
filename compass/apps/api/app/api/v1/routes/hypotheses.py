from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.hypothesis import HypothesisRead, HypothesisCreate, HypothesisUpdate
from app.repositories.hypothesis import HypothesisRepository

router = APIRouter()


@router.get("/", response_model=list[HypothesisRead])
async def list_hypotheses(
    domain: str | None = None,
    status: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[HypothesisRead]:
    repo = HypothesisRepository(db)
    return await repo.list(domain=domain, status=status, limit=limit, offset=offset)


@router.post("/", response_model=HypothesisRead, status_code=201)
async def create_hypothesis(body: HypothesisCreate, db: AsyncSession = Depends(get_db)) -> HypothesisRead:
    repo = HypothesisRepository(db)
    return await repo.create(body)


@router.get("/{hypothesis_id}", response_model=HypothesisRead)
async def get_hypothesis(hypothesis_id: UUID, db: AsyncSession = Depends(get_db)) -> HypothesisRead:
    repo = HypothesisRepository(db)
    return await repo.get_or_404(hypothesis_id)


@router.patch("/{hypothesis_id}", response_model=HypothesisRead)
async def update_hypothesis(
    hypothesis_id: UUID, body: HypothesisUpdate, db: AsyncSession = Depends(get_db)
) -> HypothesisRead:
    repo = HypothesisRepository(db)
    return await repo.update(hypothesis_id, body)


@router.post("/{hypothesis_id}/advance")
async def advance_stage(hypothesis_id: UUID, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Advance hypothesis to the next pipeline stage."""
    repo = HypothesisRepository(db)
    h = await repo.get_or_404(hypothesis_id)
    return {"hypothesis_id": str(h.id), "status": "queued"}
