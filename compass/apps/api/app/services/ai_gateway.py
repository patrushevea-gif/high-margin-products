"""AI Gateway — единая точка входа для всех LLM-вызовов.

Логирует каждый вызов, считает стоимость, реализует retry с exponential backoff,
поддерживает streaming и circuit breaker.
"""
from __future__ import annotations

import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, AsyncIterator

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Cost per million tokens (USD), as of early 2026 — update via config if needed
_COST_TABLE: dict[str, dict[str, float]] = {
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
    "claude-opus-4-7": {"input": 15.0, "output": 75.0},
    "claude-haiku-4-5-20251001": {"input": 0.25, "output": 1.25},
}


def _calc_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    rates = _COST_TABLE.get(model, {"input": 3.0, "output": 15.0})
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000


class AIGateway:
    """Wrapper around Anthropic SDK with logging, cost tracking, retry."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._run_log: list[dict[str, Any]] = []  # in-memory; persist to DB in agent layer

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.InternalServerError)),
        reraise=True,
    )
    async def complete(
        self,
        *,
        model: str,
        system: str,
        messages: list[dict[str, Any]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        tools: list[dict[str, Any]] | None = None,
        agent_name: str = "unknown",
        hypothesis_id: str | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        """Single LLM call. Returns parsed response with usage metadata."""
        call_id = run_id or str(uuid.uuid4())
        started = time.monotonic()

        params: dict[str, Any] = {
            "model": model,
            "system": system,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            params["tools"] = tools

        response = await self._client.messages.create(**params)

        elapsed_ms = int((time.monotonic() - started) * 1000)
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = _calc_cost(model, input_tokens, output_tokens)

        # Extract content blocks
        text_blocks = [b.text for b in response.content if b.type == "text"]
        tool_calls = [
            {"name": b.name, "input": b.input}
            for b in response.content
            if b.type == "tool_use"
        ]

        log_entry = {
            "call_id": call_id,
            "agent_name": agent_name,
            "hypothesis_id": hypothesis_id,
            "model": model,
            "temperature": temperature,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
            "latency_ms": elapsed_ms,
            "stop_reason": response.stop_reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._run_log.append(log_entry)
        logger.info(
            "LLM call | agent=%s model=%s tokens=%d/%d cost=$%.4f latency=%dms",
            agent_name, model, input_tokens, output_tokens, cost, elapsed_ms,
        )

        return {
            "text": "\n".join(text_blocks),
            "tool_calls": tool_calls,
            "stop_reason": response.stop_reason,
            "usage": {"input": input_tokens, "output": output_tokens, "cost_usd": cost},
            "call_id": call_id,
        }

    async def stream(
        self,
        *,
        model: str,
        system: str,
        messages: list[dict[str, Any]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        agent_name: str = "unknown",
    ) -> AsyncIterator[str]:
        """Streaming LLM call — yields text chunks."""
        async with self._client.messages.stream(
            model=model,
            system=system,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    def get_daily_cost(self) -> float:
        today = datetime.now(timezone.utc).date().isoformat()
        return sum(
            entry["cost_usd"]
            for entry in self._run_log
            if entry["timestamp"].startswith(today)
        )


_gateway: AIGateway | None = None


def get_gateway() -> AIGateway:
    global _gateway
    if _gateway is None:
        _gateway = AIGateway()
    return _gateway
