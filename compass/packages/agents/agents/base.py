"""BaseAgent — abstract parent for all Compass agents."""
from __future__ import annotations

import uuid
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """Runtime context passed to every agent run."""
    hypothesis_id: str | None = None
    source_id: str | None = None
    domain: str = "lkm"
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    auto_confirm: bool = False
    war_room: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    agent_name: str
    run_id: str
    hypothesis_id: str | None
    started_at: datetime
    finished_at: datetime
    status: str  # completed | failed | needs_confirmation
    output: dict[str, Any]
    reasoning_chain: list[dict[str, Any]]
    tokens_input: int = 0
    tokens_output: int = 0
    cost_usd: float = 0.0
    error: str | None = None


class BaseAgent(ABC):
    """Abstract base. Each agent overrides `run_pipeline`."""

    name: str = "base"
    display_name: str = "Base Agent"
    default_temperature: float = 0.3
    default_model: str = "claude-sonnet-4-6"
    allowed_tools: list[str] = []

    def __init__(
        self,
        gateway: Any,  # AIGateway, typed loosely to avoid circular import
        settings: dict[str, Any] | None = None,
    ) -> None:
        self.gateway = gateway
        self._settings = settings or {}
        self._reasoning: list[dict[str, Any]] = []

    @property
    def model(self) -> str:
        return self._settings.get("model", self.default_model)

    @property
    def temperature(self) -> float:
        return float(self._settings.get("temperature", self.default_temperature))

    @property
    def max_tokens(self) -> int:
        return int(self._settings.get("max_tokens", 4096))

    @property
    def system_prompt(self) -> str:
        return self._settings.get("system_prompt", "")

    def _log_step(self, step: str, data: dict[str, Any]) -> None:
        entry = {"step": step, "timestamp": datetime.now(timezone.utc).isoformat(), **data}
        self._reasoning.append(entry)
        logger.debug("[%s] %s: %s", self.name, step, data)

    async def run(self, ctx: AgentContext) -> AgentResult:
        self._reasoning = []
        started = datetime.now(timezone.utc)
        logger.info("Agent %s starting | run_id=%s hypothesis=%s", self.name, ctx.run_id, ctx.hypothesis_id)

        try:
            output = await self.run_pipeline(ctx)
            status = "needs_confirmation" if (not ctx.auto_confirm and output.get("requires_confirmation")) else "completed"
        except Exception as exc:
            logger.exception("Agent %s failed", self.name)
            return AgentResult(
                agent_name=self.name,
                run_id=ctx.run_id,
                hypothesis_id=ctx.hypothesis_id,
                started_at=started,
                finished_at=datetime.now(timezone.utc),
                status="failed",
                output={},
                reasoning_chain=self._reasoning,
                error=str(exc),
            )

        usage = output.pop("_usage", {"input": 0, "output": 0, "cost_usd": 0.0})
        return AgentResult(
            agent_name=self.name,
            run_id=ctx.run_id,
            hypothesis_id=ctx.hypothesis_id,
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            status=status,
            output=output,
            reasoning_chain=self._reasoning,
            tokens_input=usage.get("input", 0),
            tokens_output=usage.get("output", 0),
            cost_usd=usage.get("cost_usd", 0.0),
        )

    @abstractmethod
    async def run_pipeline(self, ctx: AgentContext) -> dict[str, Any]:
        """Agent-specific logic. Must return output dict."""
        ...
