from uuid import UUID
from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import json
from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.core.redis import get_arq_pool
from app.schemas.hypothesis import HypothesisRead, HypothesisCreate, HypothesisUpdate
from app.repositories.hypothesis import HypothesisRepository
from app.services.integrations.obsidian import get_obsidian
from app.services.integrations.bitrix24 import get_bitrix24
from app.models.hypothesis import Hypothesis, HypothesisEvaluation
from app.services.ai_gateway import get_gateway

router = APIRouter()


@router.get("/", response_model=list[HypothesisRead])
async def list_hypotheses(
    domain: str | None = None,
    status: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[HypothesisRead]:
    repo = HypothesisRepository(db)
    return await repo.list(
        domain=domain, status=status, limit=limit, offset=offset,
        org_id=user.org_id,
    )


@router.post("/", response_model=HypothesisRead, status_code=201)
async def create_hypothesis(
    body: HypothesisCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HypothesisRead:
    repo = HypothesisRepository(db)
    return await repo.create(body, org_id=user.org_id, created_by=user.user_id)


@router.get("/{hypothesis_id}", response_model=HypothesisRead)
async def get_hypothesis(
    hypothesis_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HypothesisRead:
    repo = HypothesisRepository(db)
    h = await repo.get_or_404(hypothesis_id)
    _assert_org_access(h, user)
    return h


@router.patch("/{hypothesis_id}", response_model=HypothesisRead)
async def update_hypothesis(
    hypothesis_id: UUID,
    body: HypothesisUpdate,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HypothesisRead:
    repo = HypothesisRepository(db)
    h = await repo.get_or_404(hypothesis_id)
    _assert_org_access(h, user)
    result = await repo.update(hypothesis_id, body)
    if body.status == "accepted":
        background_tasks.add_task(_on_accepted, result.model_dump())
    return result


def _assert_org_access(h: HypothesisRead, user: CurrentUser) -> None:
    """Raise 403 if the hypothesis belongs to a different org."""
    import uuid as _uuid
    h_org = h.organization_id if hasattr(h, "organization_id") else None
    if h_org is not None and user.org_id is not None and h_org != user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")


async def _on_accepted(h: dict) -> None:
    await get_obsidian().export_hypothesis(h)
    await get_bitrix24().create_task_from_hypothesis(h)


@router.get("/{hypothesis_id}/evaluations")
async def list_evaluations(
    hypothesis_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
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
    "synthesizer":     "Ты Синтезатор — старший продуктовый аналитик. Отвечаешь кратко, по делу, на русском.",
    "devils_advocate": "Ты Адвокат Дьявола — критически атакуешь идеи, ищешь слабые места. Отвечаешь на русском.",
    "market_analyst":  "Ты Рыночный Аналитик — эксперт по рынкам ЛКМ и смежным. Отвечаешь на русском.",
    "economist":       "Ты Экономист — эксперт по юнит-экономике и финансовому моделированию. Отвечаешь на русском.",
    "tech_analyst":    "Ты Технический Аналитик — эксперт по производственной реализуемости. Отвечаешь на русском.",
}


class ChatRequest(BaseModel):
    message: str
    agent: str = "synthesizer"
    history: list[dict] = []


@router.post("/{hypothesis_id}/chat")
async def chat_with_agent(
    hypothesis_id: UUID,
    body: ChatRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    repo = HypothesisRepository(db)
    h = await repo.get_or_404(hypothesis_id)
    _assert_org_access(h, user)
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


class CompareSummaryRequest(BaseModel):
    hypothesis_ids: list[str]


@router.post("/compare/summary")
async def compare_summary(
    body: CompareSummaryRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    if len(body.hypothesis_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 hypotheses to compare")
    if len(body.hypothesis_ids) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 hypotheses per comparison")

    from sqlalchemy import text as sql_text
    query = (
        "SELECT id, title, status, overall_score, confidence_score, "
        "technical, market, economics, risks FROM hypotheses WHERE id = ANY(:ids)"
    )
    params: dict = {"ids": body.hypothesis_ids}
    if user.org_id is not None:
        query += " AND organization_id = :org_id"
        params["org_id"] = str(user.org_id)

    r = await db.execute(sql_text(query), params)
    hypotheses = [dict(row) for row in r.mappings().all()]
    if not hypotheses:
        raise HTTPException(status_code=404, detail="No hypotheses found")

    gateway = get_gateway()
    prompt = (
        "Compare the following product hypotheses for a B2B chemical company "
        "(focusing on coatings/LKM and related domains). "
        "Provide a concise analytical summary in Russian (3-5 sentences) covering: "
        "which hypothesis has the best risk/margin balance, "
        "key differentiators between them, and a recommendation for which to prioritize.\n\n"
        + json.dumps(hypotheses, ensure_ascii=False, default=str, indent=2)
    )
    resp = await gateway.complete(
        model="claude-sonnet-4-6",
        system="Ты старший продуктовый аналитик B2B-химической компании. Отвечай кратко, по-русски.",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=1024,
        agent_name="compare_summary",
    )
    return {"summary": resp["text"], "cost_usd": str(resp["usage"]["cost_usd"])}


@router.post("/{hypothesis_id}/advance")
async def advance_stage(
    hypothesis_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    repo = HypothesisRepository(db)
    h = await repo.get_or_404(hypothesis_id)
    _assert_org_access(h, user)
    try:
        arq = await get_arq_pool()
        job = await arq.enqueue_job(
            "task_run_full_pipeline",
            hypothesis_id=str(h.id),
            domain=h.domain,
        )
        job_id = job.job_id if job else "unknown"
    except Exception:
        job_id = "unavailable"
    return {"hypothesis_id": str(h.id), "status": "queued", "job_id": job_id}
