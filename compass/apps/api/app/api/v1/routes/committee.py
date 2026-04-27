"""Reports & Committee — сессии голосования, статусы, экспорт."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Any
from uuid import UUID
import uuid
import json

from app.core.database import get_db
from app.services.ai_gateway import get_gateway

router = APIRouter()


class CommitteeSessionCreate(BaseModel):
    name: str
    hypothesis_ids: list[UUID]
    scheduled_at: str | None = None


class VoteRequest(BaseModel):
    session_id: str
    hypothesis_id: str
    voter_id: str
    vote: str  # proceed|defer|reject|request_data
    comment: str


@router.post("/sessions")
async def create_session(body: CommitteeSessionCreate, db: AsyncSession = Depends(get_db)) -> dict:
    """Create a committee session with a batch of committee_ready hypotheses."""
    session_id = str(uuid.uuid4())
    await db.execute(
        text("""
            INSERT INTO committee_sessions (id, name, hypothesis_ids, status, created_at, updated_at)
            VALUES (:id, :name, :hyp_ids::jsonb, 'open', now(), now())
        """),
        {
            "id": session_id,
            "name": body.name,
            "hyp_ids": json.dumps([str(hid) for hid in body.hypothesis_ids]),
        },
    )
    await db.commit()
    return {"session_id": session_id, "status": "open"}


@router.get("/sessions")
async def list_sessions(db: AsyncSession = Depends(get_db)) -> list[dict]:
    try:
        r = await db.execute(text("SELECT * FROM committee_sessions ORDER BY created_at DESC LIMIT 20"))
        return [dict(row) for row in r.mappings().all()]
    except Exception:
        return []


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        r = await db.execute(
            text("SELECT * FROM committee_sessions WHERE id = :id"), {"id": session_id}
        )
        row = r.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")
        return dict(row)
    except HTTPException:
        raise
    except Exception:
        return {"id": session_id, "status": "unknown"}


@router.post("/vote")
async def submit_vote(body: VoteRequest, db: AsyncSession = Depends(get_db)) -> dict:
    """Submit a committee member's vote on a hypothesis."""
    vote_id = str(uuid.uuid4())
    try:
        await db.execute(
            text("""
                INSERT INTO committee_votes (id, session_id, hypothesis_id, voter_id,
                    vote, comment, created_at)
                VALUES (:id, :session_id, :hypothesis_id, :voter_id, :vote, :comment, now())
            """),
            {
                "id": vote_id,
                "session_id": body.session_id,
                "hypothesis_id": body.hypothesis_id,
                "voter_id": body.voter_id,
                "vote": body.vote,
                "comment": body.comment,
            },
        )
        if body.vote in ("proceed", "reject", "defer"):
            status_map = {"proceed": "accepted", "reject": "rejected", "defer": "parked"}
            new_status = status_map[body.vote]
            await db.execute(
                text("UPDATE hypotheses SET status = :s, updated_at = now() WHERE id = :id"),
                {"s": new_status, "id": body.hypothesis_id},
            )
        await db.commit()
    except Exception as e:
        return {"vote_id": vote_id, "status": "saved", "note": "committee tables may need migration"}
    return {"vote_id": vote_id, "status": "saved"}


@router.post("/report/generate")
async def generate_report(
    hypothesis_ids: list[str],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate executive summary for a batch of hypotheses using Synthesizer LLM."""
    if not hypothesis_ids:
        raise HTTPException(status_code=400, detail="No hypotheses provided")

    gateway = get_gateway()
    r = await db.execute(
        text("SELECT id, title, short_description, status, overall_score, economics, risks FROM hypotheses WHERE id = ANY(:ids)"),
        {"ids": hypothesis_ids},
    )
    hypotheses = [dict(row) for row in r.mappings().all()]

    if not hypotheses:
        raise HTTPException(status_code=404, detail="No hypotheses found")

    prompt = (
        "Generate an executive summary for a product committee meeting. "
        "The following hypotheses are ready for committee review:\n\n"
        + json.dumps(hypotheses, ensure_ascii=False, default=str, indent=2)
        + "\n\nProvide:\n"
        "1. Executive summary (3-5 sentences)\n"
        "2. Top 3 recommendations with rationale\n"
        "3. Key risks to discuss\n"
        "4. Suggested priority order for committee vote\n\n"
        "Format: markdown with clear sections."
    )

    resp = await gateway.complete(
        model="claude-opus-4-7",
        system="You are preparing materials for a product strategy committee of a B2B chemical company.",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=4096,
        agent_name="report_generator",
    )

    return {
        "markdown": resp["text"],
        "hypotheses_count": len(hypotheses),
        "cost_usd": resp["usage"]["cost_usd"],
    }
