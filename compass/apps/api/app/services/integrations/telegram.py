"""Telegram notification service."""
from __future__ import annotations

import logging
import httpx
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self) -> None:
        settings = get_settings()
        self._token = settings.telegram_bot_token
        self._chat_id = settings.telegram_chat_id

    @property
    def _enabled(self) -> bool:
        return bool(self._token and self._chat_id)

    async def send(self, message: str, parse_mode: str = "Markdown") -> bool:
        if not self._enabled:
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"https://api.telegram.org/bot{self._token}/sendMessage",
                    json={"chat_id": self._chat_id, "text": message, "parse_mode": parse_mode},
                )
                return resp.status_code == 200
        except Exception as e:
            logger.error("Telegram: send failed: %s", e)
            return False

    async def notify_new_hypothesis(self, title: str, score: float | None, hypothesis_id: str) -> bool:
        score_text = f" · Оценка: {score:.1f}/10" if score else ""
        msg = (
            f"*Новая гипотеза готова к комитету*\n"
            f"{title}{score_text}\n"
            f"ID: `{hypothesis_id}`"
        )
        return await self.send(msg)

    async def notify_resurrection(self, title: str, trigger_type: str) -> bool:
        msg = (
            f"*Гипотеза возвращена из архива*\n"
            f"{title}\n"
            f"Триггер: {trigger_type}"
        )
        return await self.send(msg)


_notifier: TelegramNotifier | None = None


def get_telegram() -> TelegramNotifier:
    global _notifier
    if _notifier is None:
        _notifier = TelegramNotifier()
    return _notifier
