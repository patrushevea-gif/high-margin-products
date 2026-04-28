from uuid import UUID
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import json
from app.core.database import get_db
from app.schemas.hypothesis import HypothesisRead, HypothesisCreate, HypothesisUpdate
from app.repositories.hypothesis import HypothesisRepository
from app.services.integrations.obsidian import get_obsidian
from app.services.integrations.bitrix24 import get_bitrix24
from app.models.hypothesis import HypothesisEvaluation
from app.services.ai_gateway import get_gateway

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


AGENT_PERSONAS: dict[str, str] = {
    "synthesizer": "Ты Синтезатор — старший продуктовый аналитик. Отвечаешь кратко, по делу, на русском.",
    "devils_advocate": "Ты Адвокат Дьявола — критически атакуешь идеи, ищешь слабые места. Отвечаешь на русском.",
    "market_analyst": "Ты Рыночный Аналитик — эксперт по рынкам ЛКМ и смежным. Отвечаешь на русском.",
    "economist": "Ты Экономист — эксперт по юнит-экономике и финансовому моделированию. Отвечаешь на русском.",
    "tech_analyst": "Ты Технический Аналитик — эксперт по производственной реализуемости. Отвечаешь на русском.",
}


class ChatRequest(BaseModel):
    message: str
    agent: str = "synthesizer"
    history: list[dict] = []


@router.post("/{hypothesis_id}/chat")
async def chat_with_agent(
    hypothesis_id: UUID,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    repo = HypothesisRepository(db)
    h = await repo.get_or_404(hypothesis_id)
    h_dict = h.model_dump()

    persona = AGENT_PERSONAS.get(body.agent, AGENT_PERSONAS["synthesizer"])
    context = (
        f"Гипотеза: {h_dict['title']}\n"
        f"Домен: {h_dict['domain']} | Статус: {h_dict['status']}\n"
        f"Описание: {h_dict.get('short_description', '')}\n"
        f"Оценка: {h_dict.get('overall_score')} | Уверенность: {h_dict.get('confidence_score')}\n"
        f"Технический профиль: {json.dumps(h_dict.get('technical'), ensure_ascii=False)}\n"
        f"Рыночный профиль: {json.dumps(h_dict.get('market'), ensure_ascii=False)}\n"
        f"Экономика: {json.dumps(h_dict.get('economics'), ensure_ascii=False)}\n"
        f"Риски: {json.dumps(h_dict.get('risks'), ensure_ascii=False)}"
    )
    system = f"{persona}\n\nКонтекст гипотезы:\n{context}"

    messages = list(body.history) + [{"role": "user", "content": body.message}]
    gateway = get_gateway()

    async def generate():
        async for chunk in gateway.stream(
            model="claude-sonnet-4-6",
            system=system,
            messages=messages,
            temperature=0.5,
            max_tokens=1024,
            agent_name=f"chat_{body.agent}",
        ):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain")


@router.post("/{hypothesis_id}/advance")
async def advance_stage(hypothesis_id: UUID, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Queue hypothesis for next pipeline stage evaluation."""
    repo = HypothesisRepository(db)
    h = await repo.get_or_404(hypothesis_id)
    return {"hypothesis_id": str(h.id), "status": "queued"}
