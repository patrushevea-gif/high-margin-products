"""Obsidian integration — экспортирует принятые гипотезы как Markdown-заметки.

Режимы работы:
  1. Файловая система (OBSIDIAN_VAULT_PATH задан): пишет .md напрямую в vault
  2. Obsidian Local REST API plugin: POST через HTTP (если OBSIDIAN_API_URL задан)
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _build_frontmatter(h: dict[str, Any]) -> str:
    econ = h.get("economics") or {}
    risks = h.get("risks") or {}
    tags = h.get("tags") or []
    return (
        "---\n"
        f"type: hypothesis\n"
        f"id: {h.get('id', '')}\n"
        f"domain: {h.get('domain', '')}\n"
        f"status: {h.get('status', '')}\n"
        f"created: {h.get('created_at', '')[:10]}\n"
        f"margin_pct: {econ.get('margin_pct', '')}\n"
        f"risk_score: {risks.get('overall_risk_score', '')}\n"
        f"overall_score: {h.get('overall_score', '')}\n"
        f"tags: {tags}\n"
        "---\n"
    )


def _build_body(h: dict[str, Any]) -> str:
    lines = [
        f"# {h.get('title', '')}",
        "",
        h.get("short_description", ""),
        "",
    ]
    if h.get("long_description"):
        lines += [h["long_description"], ""]

    econ = h.get("economics") or {}
    if econ:
        lines += [
            "## Экономика",
            f"- Маржа: {econ.get('margin_pct', '—')}%",
            f"- Себестоимость: {econ.get('cost_per_unit_rub', '—')} ₽/ед",
            f"- Цена: {econ.get('price_per_unit_rub', '—')} ₽/ед",
            f"- Окупаемость: {econ.get('roi_months', '—')} мес",
            "",
        ]

    market = h.get("market") or {}
    if market:
        lines += [
            "## Рынок",
            f"- Объём: {market.get('market_size_mln_rub', '—')} млн ₽",
            f"- CAGR: {market.get('cagr_pct', '—')}%",
            f"- Конкуренция: {market.get('competitive_density', '—')}",
            "",
        ]

    tech = h.get("technical") or {}
    if tech:
        lines += [
            "## Технологии",
            f"- TRL: {tech.get('trl', '—')}/9",
            f"- Сложность: {tech.get('complexity', '—')}/5",
            f"- Оборудование: {tech.get('equipment_modification', '—')}",
            "",
        ]

    lines += [
        "## Метаданные",
        f"- Создана: {h.get('created_at', '')[:10]}",
        f"- Последняя оценка: {(h.get('last_evaluated_at') or '')[:10] or '—'}",
        f"- Уверенность: {round(float(h.get('confidence_score', 0)) * 100)}%",
    ]
    return "\n".join(lines)


class ObsidianExporter:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._vault_path = self._settings.obsidian_vault_path

    @property
    def _enabled(self) -> bool:
        return bool(self._vault_path)

    async def export_hypothesis(self, hypothesis: dict[str, Any]) -> bool:
        if not self._enabled:
            logger.debug("Obsidian export disabled (OBSIDIAN_VAULT_PATH not set)")
            return False

        slug = hypothesis.get("id", "unknown")[:8]
        title_safe = (hypothesis.get("title") or "")[:60].replace("/", "-").replace("\\", "-")
        filename = f"hypothesis-{slug}-{title_safe}.md"
        filepath = os.path.join(self._vault_path, "Compass", filename)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        content = _build_frontmatter(hypothesis) + "\n" + _build_body(hypothesis)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Obsidian: exported hypothesis %s to %s", hypothesis.get("id"), filepath)
            return True
        except OSError as e:
            logger.error("Obsidian: export failed: %s", e)
            return False


_exporter: ObsidianExporter | None = None


def get_obsidian() -> ObsidianExporter:
    global _exporter
    if _exporter is None:
        _exporter = ObsidianExporter()
    return _exporter
