"""Scout — непрерывный мониторинг источников, формирует raw signals."""
from __future__ import annotations

import json
import logging
from typing import Any

from agents.base import BaseAgent, AgentContext
from tools.web import TOOL_DEFINITIONS, web_fetch

logger = logging.getLogger(__name__)

_SCOUT_SYSTEM = """You are Scout, a continuous intelligence agent in the Compass system.
Your task: find fresh signals (patents, scientific publications, industry news) that could
become the basis of a new high-margin product hypothesis in the {{ domain }} domain.

Company context: B2B manufacturer of {{ domain_description }}.
Target signal characteristics: novelty, potential high margin, applicability on industrial
equipment, absence of obvious regulatory blockers.

Your output for each run must be a JSON array of RawSignal objects with fields:
- title: string (signal title)
- summary: string (2-3 sentences)
- url: string or null
- source_type: "patents" | "scientific" | "news" | "competitors"
- relevance_score: float 0-1
- relevance_rationale: string (1-2 sentences why relevant)
- domain: string (same domain as context)

Rules:
- Only include signals from the last {{ lookback_days }} days where possible.
- Do NOT assess margin or feasibility — that's for other agents.
- Prefer broader coverage over depth. Better to miss than include noise.
- Return valid JSON only in your final response, no markdown fences.
"""

_DOMAIN_DESCRIPTIONS = {
    "lkm": "paints, varnishes, and coatings (ЛКМ)",
    "soj": "cutting fluids and metalworking fluids (СОЖ)",
    "lubricants": "industrial lubricants and greases",
    "anticor": "anticorrosion coatings and inhibitors",
    "sealants": "industrial sealants",
    "adhesives": "industrial adhesives and bonding agents",
    "specialty": "specialty chemicals",
    "reagents": "chemical reagents",
    "additives": "polymer and fuel additives",
    "surfactants": "surfactants and emulsifiers",
}


class ScoutAgent(BaseAgent):
    name = "scout"
    display_name = "Scout (Разведчик)"
    default_temperature = 0.3
    default_model = "claude-sonnet-4-6"
    allowed_tools = ["web_search", "web_fetch"]

    async def run_pipeline(self, ctx: AgentContext) -> dict[str, Any]:
        domain = ctx.domain
        domain_desc = _DOMAIN_DESCRIPTIONS.get(domain, domain)
        lookback_days = 30 if not ctx.war_room else 7

        system = (
            _SCOUT_SYSTEM
            .replace("{{ domain }}", domain)
            .replace("{{ domain_description }}", domain_desc)
            .replace("{{ lookback_days }}", str(lookback_days))
        )

        messages = [
            {
                "role": "user",
                "content": (
                    f"Search for up to 15 fresh signals in the {domain} domain. "
                    f"Use web_search with queries like: "
                    f"'new {domain_desc} patents 2025 2026', "
                    f"'innovative {domain_desc} technology', "
                    f"'high margin specialty coatings research'. "
                    f"Then return a JSON array of RawSignal objects."
                ),
            }
        ]

        self._log_step("start", {"domain": domain, "lookback_days": lookback_days})

        total_usage: dict[str, Any] = {"input": 0, "output": 0, "cost_usd": 0.0}
        tool_results_messages: list[dict[str, Any]] = []
        max_tool_rounds = 5

        for round_num in range(max_tool_rounds):
            current_messages = messages + tool_results_messages
            resp = await self.gateway.complete(
                model=self.model,
                system=system,
                messages=current_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                tools=TOOL_DEFINITIONS,
                agent_name=self.name,
                hypothesis_id=ctx.hypothesis_id,
                run_id=ctx.run_id,
            )

            for k in ("input", "output", "cost_usd"):
                total_usage[k] = total_usage.get(k, 0) + resp["usage"].get(k, 0)

            self._log_step(f"llm_round_{round_num}", {
                "stop_reason": resp["stop_reason"],
                "tool_calls": len(resp["tool_calls"]),
                "text_len": len(resp["text"]),
            })

            if resp["stop_reason"] == "end_turn" or not resp["tool_calls"]:
                # Final response — parse signals
                raw_text = resp["text"].strip()
                signals = self._parse_signals(raw_text)
                self._log_step("signals_parsed", {"count": len(signals)})
                return {
                    "signals": signals,
                    "domain": domain,
                    "_usage": total_usage,
                }

            # Handle tool calls
            tool_result_content = []
            for tc in resp["tool_calls"]:
                result = await self._execute_tool(tc["name"], tc["input"])
                tool_result_content.append({
                    "type": "tool_result",
                    "tool_use_id": tc.get("id", ""),
                    "content": str(result)[:10_000],
                })

            # Add assistant message with tool_use blocks, then user message with results
            tool_results_messages.append({"role": "assistant", "content": resp.get("raw_content", resp["text"])})
            tool_results_messages.append({"role": "user", "content": tool_result_content})

        return {"signals": [], "domain": domain, "_usage": total_usage}

    async def _execute_tool(self, name: str, input_data: dict) -> str:
        self._log_step("tool_call", {"tool": name, "input": input_data})
        if name == "web_fetch":
            result = await web_fetch(input_data.get("url", ""))
            return result[:5000]
        # web_search is handled by Anthropic natively; fallback for local testing
        return json.dumps({"results": [], "note": "web_search handled by Claude"})

    def _parse_signals(self, text: str) -> list[dict[str, Any]]:
        """Extract JSON array from model response."""
        text = text.strip()
        # Find first [ ... ]
        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1:
            logger.warning("Scout: no JSON array found in response")
            return []
        try:
            signals = json.loads(text[start : end + 1])
            return [s for s in signals if isinstance(s, dict) and "title" in s]
        except json.JSONDecodeError as e:
            logger.error("Scout: JSON parse error: %s", e)
            return []
