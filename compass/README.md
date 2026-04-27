# Compass

**Continuous Opportunity Mining and Product Acceleration System**

Многоагентная система непрерывного поиска и оценки гипотез по новым высокомаржинальным продуктам для B2B-химической компании.

## Структура

```
compass/
├── apps/
│   ├── web/       # Next.js 15 frontend
│   ├── api/       # FastAPI backend
│   └── worker/    # arq background workers
├── packages/
│   ├── shared-types/  # OpenAPI-generated TS types
│   ├── agents/        # Agent definitions
│   ├── tools/         # Agent tools
│   ├── prompts/       # Jinja2 prompt templates
│   └── ui/            # Shared React components
├── infra/
│   ├── docker/        # Docker configs
│   ├── supabase/      # Migrations, RLS
│   └── github/        # CI/CD workflows
└── docs/
    ├── adr/           # Architecture Decision Records
    ├── agents/        # Agent documentation
    └── prompts/       # Prompt engineering docs
```

## Быстрый старт

```bash
cp .env.example .env
docker compose up -d
cd apps/api && uv run alembic upgrade head
cd apps/web && pnpm dev
```

## Фазы разработки

- **Фаза 1 (MVP):** Жёсткий пайплайн, 4 агента, базовый UI
- **Фаза 2:** LangGraph оркестрация, все 9 агентов, продвинутые фичи
- **Фаза 3:** 10 доменов, real API интеграции, self-hosted
