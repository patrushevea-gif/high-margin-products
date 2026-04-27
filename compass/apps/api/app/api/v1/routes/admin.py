from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()


@router.get("/stats")
async def system_stats(db: AsyncSession = Depends(get_db)) -> dict:
    """System-wide stats for admin dashboard."""
    return {
        "hypotheses_total": 0,
        "signals_total": 0,
        "agent_runs_today": 0,
        "tokens_cost_today_usd": 0.0,
    }
