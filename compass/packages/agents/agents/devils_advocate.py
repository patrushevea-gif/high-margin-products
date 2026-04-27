"""DevilsAdvocate — атакует гипотезу, ищет скрытые риски и слабые места."""
from __future__ import annotations

import json
import logging
from typing import Any

from agents.base import BaseAgent, AgentContext

logger = logging.getLogger(__name__)

_DA_SYSTEM = """You are DevilsAdvocate, a critical review agent in Compass.

Your ONLY task: find every possible reason why this hypothesis will FAIL.
You have the full analysis from TechAnalyst, MarketAnalyst, Economist, and ComplianceOfficer.

Attack the hypothesis from ALL angles:
- Technical: Is the science solid? Manufacturing feasible at scale? Equipment assumptions realistic?
- Market: Is the demand actually there? Are competitors stronger than assessed? Timing wrong?
- Economic: Are the margins sustainable? Hidden costs missed? Assumptions too optimistic?
- Legal/Compliance: Patent conflicts not caught? Regulatory blockers underestimated?
- Strategic: Fits company capabilities? Supply chain risks? Key person dependency?
- External: Macro risks (raw material prices, FX, tariffs, geopolitics)?

For each counter-argument, rate severity: minor / major / critical.
A "critical" flaw means the hypothesis should likely be rejected.

Output JSON:
{
  "counter_arguments": [
    {
      "category": "technical|market|economic|legal|strategic|external",
      "severity": "minor|major|critical",
      "argument": "Clear, specific statement of the risk or flaw",
      "evidence": "What evidence supports this counter-argument?",
      "mitigation_possible": true,
      "mitigation_hint": "How could this be addressed?"
    }
  ],
  "fatal_flaws": ["Critical flaws that could kill this hypothesis"],
  "weakest_assumption": "The single most questionable assumption in the original analysis",
  "overall_challenge_score": 1,
  "should_proceed_despite_risks": true,
  "summary": "2-3 sentence devil's advocate summary for the committee"
}

overall_challenge_score: 1 (barely challenged) to 10 (many serious flaws).
Be ruthless. Be honest. Don't soften blows. The committee needs unvarnished truth.
Return valid JSON only, no markdown.
"""


class DevilsAdvocateAgent(BaseAgent):
    name = "devils_advocate"
    display_name = "DevilsAdvocate (Адвокат дьявола)"
    default_temperature = 0.7
    default_model = "claude-opus-4-7"
    allowed_tools = []

    async def run_pipeline(self, ctx: AgentContext) -> dict[str, Any]:
        hypothesis = ctx.extra.get("hypothesis", {})
        evaluations = ctx.extra.get("evaluations", {})

        self._log_step("start", {"hypothesis_id": ctx.hypothesis_id})

        content = (
            "Attack this hypothesis. Find every reason it will fail.\n\n"
            "HYPOTHESIS:\n" + json.dumps(hypothesis, ensure_ascii=False, indent=2)
            + "\n\nALL EVALUATIONS (use these to find gaps and flaws in the analysis):\n"
            + json.dumps(evaluations, ensure_ascii=False, indent=2)
        )

        resp = await self.gateway.complete(
            model=self.model,
            system=_DA_SYSTEM,
            messages=[{"role": "user", "content": content}],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            agent_name=self.name,
            hypothesis_id=ctx.hypothesis_id,
            run_id=ctx.run_id,
        )

        self._log_step("done", {"text_len": len(resp["text"])})
        output = self._parse_output(resp["text"])
        output["_usage"] = resp["usage"]
        return output

    def _parse_output(self, text: str) -> dict[str, Any]:
        text = text.strip()
        start, end = text.find("{"), text.rfind("}")
        if start == -1:
            return {
                "counter_arguments": [],
                "should_proceed_despite_risks": True,
                "overall_challenge_score": 5,
                "summary": "Analysis unavailable",
            }
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return {
                "counter_arguments": [],
                "should_proceed_despite_risks": True,
                "overall_challenge_score": 5,
                "summary": "Parse error",
            }
