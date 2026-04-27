"""Bitrix24 integration — создаёт задачи и сделки из принятых гипотез.

Документация: https://dev.1c-bitrix.ru/rest_help/
Для включения: BITRIX24_WEBHOOK_URL должен быть заполнен в .env
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class Bitrix24Client:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._webhook = self._settings.bitrix24_webhook_url.rstrip("/")

    @property
    def _enabled(self) -> bool:
        return bool(self._webhook)

    async def create_task_from_hypothesis(self, hypothesis: dict[str, Any]) -> dict | None:
        """Создать задачу в Битрикс24 из принятой гипотезы."""
        if not self._enabled:
            logger.debug("Bitrix24 not configured — skipping task creation")
            return None

        title = hypothesis.get("title", "Новая гипотеза")
        description = (
            f"[AUTO] Гипотеза #{hypothesis.get('id', '')}\n\n"
            f"{hypothesis.get('short_description', '')}\n\n"
            f"Оценка: {hypothesis.get('overall_score', '—')}/10\n"
            f"Домен: {hypothesis.get('domain', '—')}\n"
            f"Уверенность: {round(float(hypothesis.get('confidence_score', 0)) * 100)}%\n\n"
            "Ссылка на Compass: [добавить URL]"
        )

        payload = {
            "fields": {
                "TITLE": title,
                "DESCRIPTION": description,
                "STATUS": "2",  # In Progress
                "PRIORITY": "1",
                "UF_AUTO_948000000000": hypothesis.get("id"),  # custom field for hypothesis ID
            }
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(f"{self._webhook}/tasks.task.add.json", json=payload)
                resp.raise_for_status()
                data = resp.json()
                task_id = data.get("result", {}).get("task", {}).get("id")
                logger.info("Bitrix24: created task %s for hypothesis %s", task_id, hypothesis.get("id"))
                return {"task_id": task_id}
        except Exception as e:
            logger.error("Bitrix24: failed to create task: %s", e)
            return None

    async def send_message(self, user_id: str, message: str) -> bool:
        """Отправить сообщение в чат Битрикс24."""
        if not self._enabled:
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{self._webhook}/im.message.add.json",
                    json={"DIALOG_ID": user_id, "MESSAGE": message},
                )
                return resp.status_code == 200
        except Exception as e:
            logger.error("Bitrix24: send_message failed: %s", e)
            return False


_client: Bitrix24Client | None = None


def get_bitrix24() -> Bitrix24Client:
    global _client
    if _client is None:
        _client = Bitrix24Client()
    return _client
