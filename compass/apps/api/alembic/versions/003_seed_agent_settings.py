"""Seed default agent settings

Revision ID: 003
Revises: 002
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa
import uuid
import json

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None

AGENTS = [
    {
        "agent_name": "scout",
        "display_name": "Scout (Разведчик)",
        "description": "Непрерывный мониторинг источников: патенты, статьи, новости. Формирует сырые сигналы.",
        "model": "claude-sonnet-4-6",
        "temperature": 0.3,
        "max_tokens": 8192,
        "allowed_tools": ["web_search", "web_fetch"],
        "schedule": "0 */6 * * *",
        "system_prompt": "See packages/prompts/prompts/scout.j2",
    },
    {
        "agent_name": "curator",
        "display_name": "Curator (Куратор)",
        "description": "Дедуплицирует сигналы, кластеризует их и формирует формализованные гипотезы.",
        "model": "claude-sonnet-4-6",
        "temperature": 0.4,
        "max_tokens": 4096,
        "allowed_tools": [],
        "system_prompt": "See packages/prompts/prompts/curator.j2",
    },
    {
        "agent_name": "tech_analyst",
        "display_name": "TechAnalyst (Инженер-технолог)",
        "description": "Оценивает применимость гипотезы на текущем оборудовании компании.",
        "model": "claude-sonnet-4-6",
        "temperature": 0.3,
        "max_tokens": 4096,
        "allowed_tools": [],
    },
    {
        "agent_name": "market_analyst",
        "display_name": "MarketAnalyst (Маркетолог)",
        "description": "Анализирует рыночную привлекательность, конкурентов, тренды.",
        "model": "claude-sonnet-4-6",
        "temperature": 0.5,
        "max_tokens": 4096,
        "allowed_tools": ["web_search"],
    },
    {
        "agent_name": "economist",
        "display_name": "Economist (Финансист)",
        "description": "Рассчитывает себестоимость, маржинальность, окупаемость. Monte Carlo для волатильности.",
        "model": "claude-opus-4-7",
        "temperature": 0.2,
        "max_tokens": 4096,
        "allowed_tools": ["calc_margin"],
    },
    {
        "agent_name": "compliance_officer",
        "display_name": "ComplianceOfficer (Комплаенс)",
        "description": "Проверяет стандарты, патентную чистоту, регуляторные требования.",
        "model": "claude-opus-4-7",
        "temperature": 0.2,
        "max_tokens": 4096,
        "allowed_tools": ["web_search", "check_patent_freedom"],
    },
    {
        "agent_name": "synthesizer",
        "display_name": "Synthesizer (Методист)",
        "description": "Синтезирует выводы всех агентов в итоговое заключение для комитета.",
        "model": "claude-opus-4-7",
        "temperature": 0.4,
        "max_tokens": 8192,
        "allowed_tools": [],
    },
    {
        "agent_name": "devils_advocate",
        "display_name": "DevilsAdvocate (Адвокат дьявола)",
        "description": "Атакует каждую готовую гипотезу, ищет слабые места и скрытые риски.",
        "model": "claude-opus-4-7",
        "temperature": 0.7,
        "max_tokens": 4096,
        "allowed_tools": [],
        "system_prompt": "See packages/prompts/prompts/devils_advocate.j2",
    },
    {
        "agent_name": "orchestrator",
        "display_name": "Orchestrator (Дирижёр)",
        "description": "Управляет потоком гипотез между агентами. Решает, когда нужен human-in-the-loop.",
        "model": "claude-sonnet-4-6",
        "temperature": 0.2,
        "max_tokens": 2048,
        "allowed_tools": [],
    },
]


def upgrade() -> None:
    conn = op.get_bind()
    for agent in AGENTS:
        conn.execute(
            sa.text("""
                INSERT INTO agent_settings
                    (id, agent_name, display_name, description, model, temperature,
                     max_tokens, system_prompt, allowed_tools, auto_confirm,
                     cost_limit_per_run_usd, schedule, is_active, prompt_history,
                     created_at, updated_at)
                VALUES
                    (:id, :agent_name, :display_name, :description, :model, :temperature,
                     :max_tokens, :system_prompt, :allowed_tools::jsonb, false,
                     1.0, :schedule, true, '[]'::jsonb, now(), now())
                ON CONFLICT (agent_name) DO NOTHING
            """),
            {
                "id": str(uuid.uuid4()),
                "agent_name": agent["agent_name"],
                "display_name": agent["display_name"],
                "description": agent["description"],
                "model": agent["model"],
                "temperature": agent["temperature"],
                "max_tokens": agent["max_tokens"],
                "system_prompt": agent.get("system_prompt", ""),
                "allowed_tools": json.dumps(agent.get("allowed_tools", [])),
                "schedule": agent.get("schedule"),
            },
        )


def downgrade() -> None:
    op.execute("DELETE FROM agent_settings")
