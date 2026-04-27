"""Synthesizer — финальное аналитическое заключение для комитета."""
from __future__ import annotations

import json
import logging
from typing import Any

from agents.base import BaseAgent, AgentContext

logger = logging.getLogger(__name__)

_SYNTH_SYSTEM = """You are Synthesizer, a senior analyst agent in Compass.
Collect and synthesize the evaluations from TechAnalyst, MarketAnalyst, Economist,
and ComplianceOfficer into a coherent analytical conclusion for the committee.

Your output must be a JSON object:
{
  "executive_summary": "3-5 sentences",
  "overall_score": 0.0-10.0,
  "confidence_score": 0.0-1.0,
  "key_strengths": ["..."],
  "key_risks": ["..."],
  "recommendation": "proceed|conditional|defer|reject",
  "recommendation_rationale": "...",
  "next_steps": ["..."],
  "committee_ready": true|false
}

Be balanced. Include both the opportunity case and the risk case.
Return valid JSON only, no markdown.
"""


class SynthesizerAgent(BaseAgent):
    name = "synthesizer"
    display_name = "Synthesizer (Методист)"
    default_temperature = 0.4
    default_model = "claude-opus-4-7"
    allowed_tools = []

    async def run_pipeline(self, ctx: AgentContext) -> dict[str, Any]:
        hypothesis = ctx.extra.get("hypothesis", {})
        evaluations = ctx.extra.get("evaluations", {})

        self._log_step("start", {"hypothesis_id": ctx.hypothesis_id})

        content = (
            "Synthesize a committee-ready conclusion for this hypothesis:\n\n"
            "HYPOTHESIS:\n" + json.dumps(hypothesis, ensure_ascii=False, indent=2)
            + "\n\nEVALUATIONS:\n" + json.dumps(evaluations, ensure_ascii=False, indent=2)
        )

        resp = await self.gateway.complete(
            model=self.model,
            system=_SYNTH_SYSTEM,
            messages=[{"role": "user", "content": content}],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            agent_name=self.name,
            hypothesis_id=ctx.hypothesis_id,
            run_id=ctx.run_id,
        )

        output = self._parse_output(resp["text"])
        output["_usage"] = resp["usage"]
        return output

    def _parse_output(self, text: str) -> dict[str, Any]:
        text = text.strip()
        start, end = text.find("{"), text.rfind("}")
        if start == -1:
            return {"recommendation": "defer", "committee_ready": False}
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return {"recommendation": "defer", "committee_ready": False}
