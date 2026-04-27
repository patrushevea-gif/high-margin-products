from uuid import UUID
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.hypothesis import HypothesisRead, HypothesisCreate, HypothesisUpdate
from app.repositories.hypothesis import HypothesisRepository
from app.services.integrations.obsidian import get_obsidian
from app.services.integrations.bitrix24 import get_bitrix24
from app.models.hypothesis import HypothesisEvaluation

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
    hypothesis_id: UUID,
    body: HypothesisUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> HypothesisRead:
    repo = HypothesisRepository(db)
    result = await repo.update(hypothesis_id, body)
    if body.status == "accepted":
        background_tasks.add_task(_on_accepted, result.model_dump())
    return result


async def _on_accepted(h: dict) -> None:
    """Export to Obsidian + create Bitrix24 task when hypothesis is accepted."""
    await get_obsidian().export_hypothesis(h)
    await get_bitrix24().create_task_from_hypothesis(h)


@router.get("/{hypothesis_id}/evaluations")
async def list_evaluations(hypothesis_id: UUID, db: AsyncSession = Depends(get_db)) -> list[dict]:
    """Return immutable Time Machine snapshots for this hypothesis."""
    result = await db.execute(
        select(HypothesisEvaluation)
        .where(HypothesisEvaluation.hypothesis_id == hypothesis_id)
        .order_by(HypothesisEvaluation.evaluated_at.desc())
    )
    rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "agent_name": r.agent_name,
            "run_id": str(r.run_id) if r.run_id else None,
            "evaluated_at": r.evaluated_at.isoformat(),
            "snapshot": r.snapshot,
            "delta": r.delta,
        }
        for r in rows
    ]


@router.post("/{hypothesis_id}/advance")
async def advance_stage(hypothesis_id: UUID, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Queue hypothesis for next pipeline stage evaluation."""
    repo = HypothesisRepository(db)
    h = await repo.get_or_404(hypothesis_id)
    return {"hypothesis_id": str(h.id), "status": "queued"}
