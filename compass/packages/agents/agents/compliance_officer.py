"""ComplianceOfficer — стандарты, патентная чистота, регуляторные риски."""
from __future__ import annotations

import json
import logging
from typing import Any

from agents.base import BaseAgent, AgentContext
from tools.web import TOOL_DEFINITIONS

logger = logging.getLogger(__name__)

_COMPLIANCE_SYSTEM = """You are ComplianceOfficer, a regulatory and legal agent in Compass.
Check compliance of the given hypothesis for a B2B chemical manufacturer.

Your assessment must cover:
1. Applicable quality standards (ISO, ГОСТ, EN)
2. Safety & environmental standards (REACH, GHS, СанПиН, ФЗ)
3. Patent landscape: are there active patents blocking this product?
4. Certification requirements and timeline (Russia + target export markets)
5. Import/export restrictions on materials or finished products
6. Regulatory change risk: upcoming regulation changes that could affect this product

For each risk area, rate severity: none / low / medium / high / critical.

Output JSON:
{
  "applicable_standards": [
    {"code": "ГОСТ Р ...", "description": "...", "mandatory": true}
  ],
  "patent_risk": {
    "level": "none|low|medium|high|critical",
    "blocking_patents": [],
    "expiring_patents": [],
    "freedom_to_operate": true,
    "notes": "..."
  },
  "regulatory_risk": {
    "level": "none|low|medium|high|critical",
    "issues": [],
    "notes": "..."
  },
  "certification_timeline_months": 0,
  "certification_cost_mln_rub": 0.0,
  "import_restrictions": [],
  "upcoming_regulatory_changes": [],
  "overall_compliance_verdict": "clear|conditional|blocked",
  "confidence": 0.0,
  "recommendations": ["..."]
}

Use web_search to find relevant standards and recent patent activity.
Return valid JSON only, no markdown.
"""


class ComplianceOfficerAgent(BaseAgent):
    name = "compliance_officer"
    display_name = "ComplianceOfficer (Комплаенс)"
    default_temperature = 0.2
    default_model = "claude-opus-4-7"
    allowed_tools = ["web_search", "web_fetch"]

    async def run_pipeline(self, ctx: AgentContext) -> dict[str, Any]:
        hypothesis = ctx.extra.get("hypothesis", {})
        domain = ctx.domain

        self._log_step("start", {"hypothesis_title": hypothesis.get("title", "")})

        messages = [{
            "role": "user",
            "content": (
                f"Perform compliance check for this hypothesis in domain '{domain}':\n\n"
                + json.dumps(hypothesis, ensure_ascii=False, indent=2)
                + "\n\nSearch for applicable GOST/ISO standards, patents, and regulatory requirements."
            ),
        }]

        tool_results: list[dict[str, Any]] = []
        max_rounds = 4

        for round_num in range(max_rounds):
            resp = await self.gateway.complete(
                model=self.model,
                system=_COMPLIANCE_SYSTEM,
                messages=messages + tool_results,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                tools=TOOL_DEFINITIONS,
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
                tool_results.append({
                    "role": "assistant",
                    "content": f"[{tc['name']} called: {tc['input']}]",
                })
                tool_results.append({
                    "role": "user",
                    "content": f"Tool result: [compliance/standard data for query]",
                })

        return {"overall_compliance_verdict": "unknown", "confidence": 0.0, "_usage": {"input": 0, "output": 0, "cost_usd": 0.0}}

    def _parse_output(self, text: str) -> dict[str, Any]:
        text = text.strip()
        start, end = text.find("{"), text.rfind("}")
        if start == -1:
            return {"overall_compliance_verdict": "unknown", "confidence": 0.0}
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return {"overall_compliance_verdict": "unknown", "confidence": 0.0}
