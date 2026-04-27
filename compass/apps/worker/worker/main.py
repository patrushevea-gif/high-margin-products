"""arq worker entrypoint — all tasks and cron jobs."""
from __future__ import annotations

import os
import sys
import logging

sys.path.insert(0, "/packages/agents")
sys.path.insert(0, "/packages/tools")

from arq import cron
from arq.connections import RedisSettings

from worker.pipeline import (
    task_scout_run,
    task_curator_run,
    task_evaluate_tech,
    task_evaluate_market,
    task_evaluate_economics,
    task_evaluate_compliance,
    task_synthesize,
    task_devils_advocate,
    task_run_full_pipeline,
    task_scout_and_process,
)
from worker.resurrection import task_scan_resurrection_triggers

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


async def startup(ctx: dict) -> None:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    engine = create_async_engine(os.environ["DATABASE_URL"], pool_pre_ping=True, pool_size=5)
    ctx["db_sessionmaker"] = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    ctx["db"] = ctx["db_sessionmaker"]()

    # AI Gateway — lazy import to keep worker lightweight
    sys.path.insert(0, "/app")
    from app.services.ai_gateway import get_gateway
    ctx["ai_gateway"] = get_gateway()

    logger.info("Compass worker started")


async def shutdown(ctx: dict) -> None:
    if "db" in ctx:
        await ctx["db"].close()
    logger.info("Compass worker stopped")


# ─── Cron jobs ───────────────────────────────────────────────────────────────

async def cron_scout_lkm(ctx: dict) -> None:
    """Scout + full pipeline for LKM domain, every 6 hours."""
    logger.info("Cron: scout LKM")
    await task_scout_and_process(ctx, domain="lkm")


async def cron_resurrection_scan(ctx: dict) -> None:
    """Scan resurrection triggers for rejected hypotheses, daily."""
    logger.info("Cron: resurrection scan")
    await task_scan_resurrection_triggers(ctx)


class WorkerSettings:
    functions = [
        task_scout_run,
        task_curator_run,
        task_evaluate_tech,
        task_evaluate_market,
        task_evaluate_economics,
        task_evaluate_compliance,
        task_synthesize,
        task_devils_advocate,
        task_run_full_pipeline,
        task_scout_and_process,
        task_scan_resurrection_triggers,
    ]
    cron_jobs = [
        cron(cron_scout_lkm, hour={0, 6, 12, 18}, minute=0),
        cron(cron_resurrection_scan, hour=3, minute=0),
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(os.environ.get("REDIS_URL", "redis://redis:6379"))
    max_jobs = 10
    job_timeout = 900  # 15 min
    keep_result = 3600
