# ADR 001: Technology Stack

## Status
Accepted

## Context
Need to choose a technology stack for Compass — a multi-agent AI system for high-margin product discovery.

## Decision

### Frontend
- **Next.js 15** (App Router) — mature, server components, streaming
- **TailwindCSS** + CSS variables — dark theme, design tokens
- **TanStack Query** — async state, caching, refetch
- **@xyflow/react** — agent process map visualization
- **cmdk** — command palette

### Backend
- **FastAPI + Python 3.12** — AI ecosystem, async, typed
- **SQLAlchemy 2 async + Alembic** — ORM + migrations
- **PostgreSQL 16 + pgvector** — relational + vector search in one system
- **arq** over Celery — simpler, async-native, Redis-based

### AI Layer
- **Anthropic Claude** — primary LLM (Sonnet for most, Opus for complex analysis)
- Custom **AI Gateway** wrapper — logging, cost tracking, retry, streaming

### Infrastructure
- Docker Compose for local dev
- Supabase for MVP (Auth + managed Postgres)
- GitHub Actions for CI/CD

## Consequences
- Python AI ecosystem provides better LLM tooling than TypeScript
- pgvector avoids a separate vector DB (Pinecone, Weaviate etc.)
- arq is simpler than Celery but has fewer features (acceptable for Phase 1)
