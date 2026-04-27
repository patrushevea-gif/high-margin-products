"""TechAnalyst — оценивает применимость на оборудовании компании."""
from __future__ import annotations

import json
import logging
from typing import Any

from agents.base import BaseAgent, AgentContext

logger = logging.getLogger(__name__)

_TECH_SYSTEM = """You are TechAnalyst, a process engineer agent in Compass.
Evaluate the technical feasibility of the given hypothesis for a B2B chemical manufacturer
specializing in {{ domain }}.

Assess:
1. Equipment complexity (1=simple, 5=very complex)
2. Equipment modification required (none/minor/major/new)
3. Raw material availability (available/partial/closed)
4. Technology Readiness Level (TRL 1-9)
5. Key technical risks and blockers
6. Recommended next steps for technical validation

Output a JSON object:
{
  "complexity": 1-5,
  "equipment_modification": "none|minor|major|new",
  "raw_material_availability": "available|partial|closed",
  "trl": 1-9,
  "technical_risks": ["..."],
  "blockers": ["..."],
  "notes": "...",
  "verdict": "feasible|conditional|not_feasible",
  "confidence": 0.0-1.0
}

Be honest about uncertainty. Low confidence = say so.
Return valid JSON only, no markdown.
"""


class TechAnalystAgent(BaseAgent):
    name = "tech_analyst"
    display_name = "TechAnalyst (Инженер-технолог)"
    default_temperature = 0.3
    default_model = "claude-sonnet-4-6"
    allowed_tools = []

    async def run_pipeline(self, ctx: AgentContext) -> dict[str, Any]:
        hypothesis = ctx.extra.get("hypothesis", {})
        domain = ctx.domain

        self._log_step("start", {"hypothesis_title": hypothesis.get("title", "")})

        resp = await self.gateway.complete(
            model=self.model,
            system=_TECH_SYSTEM.replace("{{ domain }}", domain),
            messages=[{
                "role": "user",
                "content": (
                    "Evaluate the technical feasibility of this hypothesis:\n\n"
                    + json.dumps(hypothesis, ensure_ascii=False, indent=2)
                ),
            }],
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
            return {"verdict": "unknown", "confidence": 0.0}
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return {"verdict": "unknown", "confidence": 0.0}
