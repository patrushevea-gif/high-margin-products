"""Counterfactual Engine — «А что если...» для любой гипотезы."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Any
from uuid import UUID
import json

from app.core.database import get_db
from app.services.ai_gateway import get_gateway

router = APIRouter()


class CounterfactualScenario(BaseModel):
    name: str
    changes: list[dict[str, Any]]  # [{type, target, operator, value, unit}]


class CounterfactualRequest(BaseModel):
    hypothesis_ids: list[UUID]
    scenario: CounterfactualScenario
    include_rejected: bool = True


class CounterfactualResult(BaseModel):
    hypothesis_id: str
    title: str
    original_status: str
    original_score: float | None
    scenario_score: float | None
    delta: float | None
    flip: bool  # True if verdict changed (rejected→viable or vice versa)
    explanation: str


@router.post("/analyze", response_model=list[CounterfactualResult])
async def analyze_counterfactual(
    body: CounterfactualRequest,
    db: AsyncSession = Depends(get_db),
) -> list[CounterfactualResult]:
    """
    Re-evaluate hypotheses under the given scenario.
    This runs a quick LLM estimation, NOT a full pipeline re-run.
    Results are NOT saved to the main hypothesis record.
    """
    gateway = get_gateway()

    ids = [str(hid) for hid in body.hypothesis_ids]
    r = await db.execute(
        text("SELECT id, title, status, overall_score, economics, risks FROM hypotheses WHERE id = ANY(:ids)"),
        {"ids": ids},
    )
    hypotheses = [dict(row) for row in r.mappings().all()]

    results: list[CounterfactualResult] = []

    for h in hypotheses:
        prompt = (
            f"Hypothesis: {h['title']}\n"
            f"Current status: {h['status']}\n"
            f"Current overall score: {h.get('overall_score', 'unknown')}\n\n"
            f"Economics: {json.dumps(h.get('economics'), ensure_ascii=False)}\n"
            f"Risks: {json.dumps(h.get('risks'), ensure_ascii=False)}\n\n"
            f"Counterfactual scenario '{body.scenario.name}':\n"
            + json.dumps(body.scenario.changes, ensure_ascii=False, indent=2)
            + "\n\nHow does this scenario change the viability of this hypothesis? "
            "Give a revised overall_score (0-10) and a 1-sentence explanation. "
            "Respond in JSON: {\"score\": 7.2, \"explanation\": \"...\"}"
        )

        resp = await gateway.complete(
            model="claude-sonnet-4-6",
            system="You are a business analyst evaluating counterfactual scenarios for product hypotheses.",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=512,
            agent_name="counterfactual",
        )

        scenario_score: float | None = None
        explanation = ""
        try:
            text_resp = resp["text"]
            start = text_resp.find("{")
            end = text_resp.rfind("}")
            if start != -1:
                parsed = json.loads(text_resp[start:end + 1])
                scenario_score = float(parsed.get("score", 0))
                explanation = parsed.get("explanation", "")
        except Exception:
            explanation = resp["text"][:200]

        original_score = h.get("overall_score")
        delta = (scenario_score - original_score) if (scenario_score is not None and original_score is not None) else None
        flip = delta is not None and abs(delta) >= 2.0

        results.append(CounterfactualResult(
            hypothesis_id=str(h["id"]),
            title=h["title"],
            original_status=h["status"],
            original_score=original_score,
            scenario_score=scenario_score,
            delta=delta,
            flip=flip,
            explanation=explanation,
        ))

    results.sort(key=lambda x: (x.flip, abs(x.delta or 0)), reverse=True)
    return results


@router.get("/scenarios")
async def list_saved_scenarios(db: AsyncSession = Depends(get_db)) -> list[dict]:
    """List saved (named) counterfactual scenarios — stub, table added in future migration."""
    return []
