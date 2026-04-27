"""Memory Resurrection — ежедневный сканер триггеров для отвергнутых гипотез.

Триггеры:
  - price_change: цена сырья упала ниже порога
  - patent_expiry: патент истёк
  - regulation_change: ключевое слово в свежих регуляторных новостях
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone, date
from typing import Any

logger = logging.getLogger(__name__)


async def task_scan_resurrection_triggers(ctx: dict) -> dict:
    db = ctx["db"]
    revived: list[str] = []

    from sqlalchemy import text

    result = await db.execute(
        text("""
            SELECT id, title, resurrection_triggers
            FROM hypotheses
            WHERE status = 'rejected'
              AND resurrection_triggers IS NOT NULL
              AND resurrection_triggers != '[]'::jsonb
        """)
    )
    rows = result.mappings().all()

    for row in rows:
        hid = str(row["id"])
        triggers = row["resurrection_triggers"]
        if isinstance(triggers, str):
            triggers = json.loads(triggers)

        triggered_by: list[str] = []

        for t in triggers:
            fired = await _evaluate_trigger(ctx, t)
            if fired:
                triggered_by.append(t.get("type", "unknown"))

        if triggered_by:
            reason = f"Возвращена из архива по триггеру: {', '.join(triggered_by)}"
            await db.execute(
                text("""
                    UPDATE hypotheses
                    SET status = 'to_review',
                        tags = tags || :tag::jsonb,
                        updated_at = now()
                    WHERE id = :id
                """),
                {"id": hid, "tag": json.dumps([f"resurrected:{date.today().isoformat()}"])},
            )
            await db.commit()
            revived.append(hid)
            logger.info("Resurrected hypothesis %s: %s", hid, reason)

    logger.info("Resurrection scan done: %d revived", len(revived))
    return {"revived_count": len(revived), "revived_ids": revived}


async def _evaluate_trigger(ctx: dict, trigger: dict) -> bool:
    """Check if a single trigger has fired. Returns True if it should revive the hypothesis."""
    t_type = trigger.get("type")

    if t_type == "patent_expiry":
        expiry_str = trigger.get("expiry_after")
        if expiry_str:
            expiry_date = date.fromisoformat(expiry_str)
            return date.today() >= expiry_date

    if t_type == "price_change":
        # Stub: in real implementation would call commodity price API
        # For now, always returns False (trigger never fires without real data)
        return False

    if t_type == "regulation_change":
        # Stub: would search recent regulatory news for keyword
        # keyword = trigger.get("keyword", "")
        return False

    return False
