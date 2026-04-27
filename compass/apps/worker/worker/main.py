"""arq worker entrypoint."""
from __future__ import annotations

import logging
import sys
from typing import Any

sys.path.insert(0, "/packages/agents")
sys.path.insert(0, "/packages/tools")

from arq import cron
from arq.connections import RedisSettings

from worker.pipeline import (
    task_scout_run,
    task_curator_run,
    task_evaluate_hypothesis,
    task_synthesize_hypothesis,
)

logger = logging.getLogger(__name__)


async def startup(ctx: dict) -> None:
    import os
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    engine = create_async_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    ctx["db_sessionmaker"] = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create one shared session for worker context
    ctx["db"] = ctx["db_sessionmaker"]()

    # AI Gateway
    sys.path.insert(0, "/app")
    from app.services.ai_gateway import get_gateway
    ctx["ai_gateway"] = get_gateway()

    logger.info("Worker started")


async def shutdown(ctx: dict) -> None:
    if "db" in ctx:
        await ctx["db"].close()
    logger.info("Worker stopped")


async def scheduled_scout_lkm(ctx: dict) -> None:
    """Cron job: run Scout for LKM domain every 6 hours."""
    logger.info("Scheduled Scout run for LKM")
    result = await task_scout_run(ctx, domain="lkm")
    signals = result.get("signals", [])
    if signals:
        await task_curator_run(ctx, signals=signals, domain="lkm")


class WorkerSettings:
    functions = [
        task_scout_run,
        task_curator_run,
        task_evaluate_hypothesis,
        task_synthesize_hypothesis,
    ]
    cron_jobs = [
        cron(scheduled_scout_lkm, hour={0, 6, 12, 18}, minute=0),
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn("redis://redis:6379")
    max_jobs = 10
    job_timeout = 600  # 10 min
    keep_result = 3600
