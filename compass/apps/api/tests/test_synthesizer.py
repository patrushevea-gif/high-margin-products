"""Tests for SynthesizerAgent with mocked AIGateway."""
import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock

# Make packages/agents importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../packages/agents"))

from agents.synthesizer import SynthesizerAgent
from agents.base import AgentContext


VALID_OUTPUT = """{
  "executive_summary": "Перспективная ниша с умеренными рисками.",
  "overall_score": 7.5,
  "confidence_score": 0.78,
  "key_strengths": ["Высокая маржа", "Дефицит предложения"],
  "key_risks": ["Патентные риски"],
  "recommendation": "proceed",
  "recommendation_rationale": "Рынок готов.",
  "next_steps": ["Провести пилот"],
  "committee_ready": true
}"""


def _make_gateway(text: str) -> MagicMock:
    gw = MagicMock()
    gw.complete = AsyncMock(return_value={
        "text": text,
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 100, "output_tokens": 200},
        "cost_usd": 0.005,
    })
    return gw


def _make_ctx(**kwargs) -> AgentContext:
    return AgentContext(
        hypothesis_id="test-hyp-id",
        domain="lkm",
        extra={
            "hypothesis": {"title": "Тест", "domain": "lkm"},
            "evaluations": {"tech": {"complexity": 3}, "market": {"market_size_mln_rub": 500}},
            **kwargs,
        },
    )


@pytest.mark.anyio
async def test_synthesizer_happy_path():
    agent = SynthesizerAgent(gateway=_make_gateway(VALID_OUTPUT))
    ctx = _make_ctx()
    result = await agent.run(ctx)
    assert result.status == "success"
    assert result.output["overall_score"] == 7.5
    assert result.output["recommendation"] == "proceed"
    assert result.output["committee_ready"] is True


@pytest.mark.anyio
async def test_synthesizer_returns_usage():
    agent = SynthesizerAgent(gateway=_make_gateway(VALID_OUTPUT))
    result = await agent.run(_make_ctx())
    assert "_usage" in result.output
    assert result.output["_usage"]["input_tokens"] == 100


@pytest.mark.anyio
async def test_synthesizer_invalid_json_fallback():
    agent = SynthesizerAgent(gateway=_make_gateway("Не JSON ответ"))
    result = await agent.run(_make_ctx())
    assert result.output["recommendation"] == "defer"
    assert result.output["committee_ready"] is False


@pytest.mark.anyio
async def test_synthesizer_partial_json():
    partial = '{"overall_score": 6.0, "recommendation": "conditional", "committee_ready": false}'
    agent = SynthesizerAgent(gateway=_make_gateway(partial))
    result = await agent.run(_make_ctx())
    assert result.output["overall_score"] == 6.0
    assert result.output["committee_ready"] is False


@pytest.mark.anyio
async def test_synthesizer_calls_gateway_once():
    gw = _make_gateway(VALID_OUTPUT)
    agent = SynthesizerAgent(gateway=gw)
    await agent.run(_make_ctx())
    gw.complete.assert_called_once()


@pytest.mark.anyio
async def test_synthesizer_gateway_error_handled():
    gw = MagicMock()
    gw.complete = AsyncMock(side_effect=RuntimeError("API down"))
    agent = SynthesizerAgent(gateway=gw)
    result = await agent.run(_make_ctx())
    assert result.status == "failed"
    assert "API down" in result.error
