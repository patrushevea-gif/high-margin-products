"""MarketAnalyst — анализирует рыночную привлекательность гипотезы."""
from __future__ import annotations

import json
import logging
from typing import Any

from agents.base import BaseAgent, AgentContext
from tools.web import TOOL_DEFINITIONS

logger = logging.getLogger(__name__)

_MARKET_SYSTEM = """You are MarketAnalyst, a market intelligence agent in Compass.
Analyze the market attractiveness of the given hypothesis for a B2B chemical manufacturer.

Research and assess:
1. Market size (in million RUB/year for Russia, and global if relevant)
2. Market growth rate (CAGR %)
3. Competitive density (low/medium/high) + key competitors
4. Target customer segments (industrial, automotive, construction, etc.)
5. Geographic focus (Russia/CIS, EU, global)
6. Key market trends driving demand
7. Barriers to entry
8. Pricing dynamics: typical price range, margin expectations in the segment

Output JSON:
{
  "market_size_mln_rub": 0.0,
  "cagr_pct": 0.0,
  "competitive_density": "low|medium|high",
  "key_competitors": ["Company A", "Company B"],
  "target_segments": ["segment1", "segment2"],
  "geographic_focus": ["Russia", "CIS"],
  "key_trends": ["trend1", "trend2"],
  "barriers_to_entry": ["barrier1"],
  "price_range_rub_per_unit": {"min": 0, "max": 0, "unit": "kg|liter|set"},
  "expected_margin_pct": 0.0,
  "market_verdict": "attractive|moderate|unattractive",
  "confidence": 0.0,
  "notes": "..."
}

Use web_search to find real market data. Prefer recent sources (2024-2026).
Return valid JSON only, no markdown.
"""


class MarketAnalystAgent(BaseAgent):
    name = "market_analyst"
    display_name = "MarketAnalyst (Маркетолог)"
    default_temperature = 0.5
    default_model = "claude-sonnet-4-6"
    allowed_tools = ["web_search"]

    async def run_pipeline(self, ctx: AgentContext) -> dict[str, Any]:
        hypothesis = ctx.extra.get("hypothesis", {})
        domain = ctx.domain

        self._log_step("start", {"hypothesis_title": hypothesis.get("title", "")})

        messages = [{
            "role": "user",
            "content": (
                f"Analyze market attractiveness for this hypothesis in domain '{domain}':\n\n"
                + json.dumps(hypothesis, ensure_ascii=False, indent=2)
                + "\n\nSearch for market size, competitors, and trends. Then provide your analysis."
            ),
        }]

        tool_results: list[dict[str, Any]] = []
        max_rounds = 3

        for round_num in range(max_rounds):
            resp = await self.gateway.complete(
                model=self.model,
                system=_MARKET_SYSTEM,
                messages=messages + tool_results,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                tools=TOOL_DEFINITIONS,
                agent_name=self.name,
                hypothesis_id=ctx.hypothesis_id,
                run_id=ctx.run_id,
            )

            self._log_step(f"round_{round_num}", {
                "stop_reason": resp["stop_reason"],
                "tool_calls": len(resp["tool_calls"]),
            })

            if resp["stop_reason"] == "end_turn" or not resp["tool_calls"]:
                output = self._parse_output(resp["text"])
                output["_usage"] = resp["usage"]
                return output

            for tc in resp["tool_calls"]:
                tool_results.append({
                    "role": "assistant",
                    "content": f"[searched: {tc['input'].get('query', '')}]",
                })
                tool_results.append({
                    "role": "user",
                    "content": f"Search results for '{tc['input'].get('query', '')}': [market data would appear here]",
                })

        return {"market_verdict": "unknown", "confidence": 0.0, "_usage": {"input": 0, "output": 0, "cost_usd": 0.0}}

    def _parse_output(self, text: str) -> dict[str, Any]:
        text = text.strip()
        start, end = text.find("{"), text.rfind("}")
        if start == -1:
            return {"market_verdict": "unknown", "confidence": 0.0}
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return {"market_verdict": "unknown", "confidence": 0.0}
