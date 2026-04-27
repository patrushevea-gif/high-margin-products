"""Economist — рассчитывает себестоимость, маржинальность, окупаемость."""
from __future__ import annotations

import json
import logging
from typing import Any

from agents.base import BaseAgent, AgentContext
from tools.calc import calc_margin, CALC_MARGIN_TOOL

logger = logging.getLogger(__name__)

_ECON_SYSTEM = """You are Economist, a financial analyst agent in Compass.
Calculate cost structure, margins, and ROI for the given hypothesis.

Your analysis must include:
1. Estimated cost per unit (raw materials + energy + labor + overhead)
2. Expected market price per unit
3. Gross margin %
4. Break-even volume (units/year)
5. Investment required for launch (equipment, certification, working capital)
6. Payback period (months)
7. Sensitivity analysis: what happens if raw material cost +20%, price -10%?
8. Risk flags: commodity price volatility, FX exposure

Use calc_margin tool to run Monte Carlo simulation on margin under volatility.

Output JSON:
{
  "cost_per_unit_rub": 0.0,
  "price_per_unit_rub": 0.0,
  "margin_pct": 0.0,
  "margin_rub_per_unit": 0.0,
  "min_batch_units": 0,
  "roi_months": 0,
  "breakeven_units_year": 0,
  "investment_required_mln_rub": 0.0,
  "monte_carlo": {
    "p10_margin_pct": 0.0,
    "p50_margin_pct": 0.0,
    "p90_margin_pct": 0.0
  },
  "sensitivity": {
    "cost_plus_20pct_margin": 0.0,
    "price_minus_10pct_margin": 0.0
  },
  "risk_flags": ["..."],
  "economic_verdict": "viable|marginal|not_viable",
  "confidence": 0.0,
  "assumptions": "..."
}

Return valid JSON only. Be conservative in estimates — it's better to underpromise.
"""

_CALC_TOOL_DEF = {
    "name": "calc_margin",
    "description": "Calculate margin with Monte Carlo simulation for price/cost volatility",
    "input_schema": {
        "type": "object",
        "properties": {
            "cost_per_unit": {"type": "number"},
            "market_price": {"type": "number"},
            "volume_units_annual": {"type": "integer"},
            "cost_volatility_pct": {"type": "number", "default": 10},
            "price_volatility_pct": {"type": "number", "default": 5},
        },
        "required": ["cost_per_unit", "market_price", "volume_units_annual"],
    },
}


class EconomistAgent(BaseAgent):
    name = "economist"
    display_name = "Economist (Финансист)"
    default_temperature = 0.2
    default_model = "claude-opus-4-7"
    allowed_tools = ["calc_margin"]

    async def run_pipeline(self, ctx: AgentContext) -> dict[str, Any]:
        hypothesis = ctx.extra.get("hypothesis", {})
        market_data = ctx.extra.get("market_evaluation", {})

        self._log_step("start", {"hypothesis_title": hypothesis.get("title", "")})

        messages = [{
            "role": "user",
            "content": (
                "Calculate economics for this hypothesis:\n\n"
                "HYPOTHESIS:\n" + json.dumps(hypothesis, ensure_ascii=False, indent=2)
                + "\n\nMARKET DATA:\n" + json.dumps(market_data, ensure_ascii=False, indent=2)
                + "\n\nUse calc_margin to run Monte Carlo. Be specific with numbers."
            ),
        }]

        tool_results: list[dict[str, Any]] = []
        max_rounds = 4

        for round_num in range(max_rounds):
            resp = await self.gateway.complete(
                model=self.model,
                system=_ECON_SYSTEM,
                messages=messages + tool_results,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                tools=[_CALC_TOOL_DEF],
                agent_name=self.name,
                hypothesis_id=ctx.hypothesis_id,
                run_id=ctx.run_id,
            )

            self._log_step(f"round_{round_num}", {"stop_reason": resp["stop_reason"]})

            if resp["stop_reason"] == "end_turn" or not resp["tool_calls"]:
                output = self._parse_output(resp["text"])
                output["_usage"] = resp["usage"]
                return output

            for tc in resp["tool_calls"]:
                if tc["name"] == "calc_margin":
                    calc_result = calc_margin(**{
                        k: v for k, v in tc["input"].items()
                        if k in ("cost_per_unit", "market_price", "volume_units_annual",
                                 "cost_volatility_pct", "price_volatility_pct", "simulations")
                    })
                    tool_results.append({
                        "role": "assistant",
                        "content": f"[calc_margin called with {tc['input']}]",
                    })
                    tool_results.append({
                        "role": "user",
                        "content": f"calc_margin result: {json.dumps(calc_result)}",
                    })

        return {"economic_verdict": "unknown", "confidence": 0.0, "_usage": {"input": 0, "output": 0, "cost_usd": 0.0}}

    def _parse_output(self, text: str) -> dict[str, Any]:
        text = text.strip()
        start, end = text.find("{"), text.rfind("}")
        if start == -1:
            return {"economic_verdict": "unknown", "confidence": 0.0}
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return {"economic_verdict": "unknown", "confidence": 0.0}
