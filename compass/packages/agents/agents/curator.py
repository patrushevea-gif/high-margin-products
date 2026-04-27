"""Curator — дедуплицирует сигналы и формирует гипотезы."""
from __future__ import annotations

import json
import logging
from typing import Any

from agents.base import BaseAgent, AgentContext

logger = logging.getLogger(__name__)

_CURATOR_SYSTEM = """You are Curator, a signal processing agent in the Compass system.
Your task: take a list of raw signals and:
1. Remove duplicates (same concept, different sources — keep the best one).
2. Cluster related signals into groups.
3. For each cluster with ≥1 high-relevance signal (relevance_score > 0.6), form a
   structured hypothesis draft.

Output a JSON object:
{
  "hypotheses": [
    {
      "title": "...",
      "short_description": "2-3 sentences",
      "source_type": "...",
      "relevance_score": 0.0-1.0,
      "source_signal_titles": ["...", "..."],
      "domain": "..."
    }
  ],
  "deduplicated_count": 0,
  "clusters_found": 0
}

Be selective. Only form hypotheses from genuinely interesting signal clusters.
Return valid JSON only, no markdown.
"""


class CuratorAgent(BaseAgent):
    name = "curator"
    display_name = "Curator (Куратор)"
    default_temperature = 0.4
    default_model = "claude-sonnet-4-6"
    allowed_tools = []

    async def run_pipeline(self, ctx: AgentContext) -> dict[str, Any]:
        signals: list[dict] = ctx.extra.get("signals", [])
        if not signals:
            return {"hypotheses": [], "_usage": {"input": 0, "output": 0, "cost_usd": 0.0}}

        self._log_step("start", {"signals_count": len(signals)})

        resp = await self.gateway.complete(
            model=self.model,
            system=_CURATOR_SYSTEM,
            messages=[{
                "role": "user",
                "content": (
                    f"Process these {len(signals)} raw signals from domain '{ctx.domain}':\n\n"
                    + json.dumps(signals, ensure_ascii=False, indent=2)
                ),
            }],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            agent_name=self.name,
            hypothesis_id=ctx.hypothesis_id,
            run_id=ctx.run_id,
        )

        output = self._parse_output(resp["text"])
        self._log_step("done", {"hypotheses": len(output.get("hypotheses", []))})
        output["_usage"] = resp["usage"]
        return output

    def _parse_output(self, text: str) -> dict[str, Any]:
        text = text.strip()
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return {"hypotheses": []}
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return {"hypotheses": []}
