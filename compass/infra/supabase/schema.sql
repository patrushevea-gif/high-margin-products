-- ============================================================
-- Compass — полная схема БД для Supabase SQL Editor
-- Вставь всё целиком в SQL Editor и нажми Run
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── sources ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sources (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(200) NOT NULL,
  url_pattern VARCHAR(2000),
  source_type VARCHAR(50) NOT NULL,
  domain VARCHAR(50) NOT NULL DEFAULT 'lkm',
  parsing_strategy VARCHAR(50) DEFAULT 'ai',
  selectors_hint TEXT,
  rate_limit_rpm INTEGER DEFAULT 10,
  api_endpoint VARCHAR(2000),
  api_auth JSONB,
  api_schema_mapping JSONB,
  prefer_api BOOLEAN DEFAULT false,
  schedule VARCHAR(100) DEFAULT '0 */6 * * *',
  is_active BOOLEAN DEFAULT true,
  last_run_at TIMESTAMPTZ,
  last_run_success BOOLEAN,
  last_run_signals INTEGER DEFAULT 0,
  tokens_used_month INTEGER DEFAULT 0,
  cost_usd_month FLOAT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ── hypotheses ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS hypotheses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title VARCHAR(500) NOT NULL,
  short_description TEXT NOT NULL,
  long_description TEXT,
  domain VARCHAR(50) NOT NULL DEFAULT 'lkm',
  status VARCHAR(50) NOT NULL DEFAULT 'draft',
  curator_id UUID,
  technical JSONB,
  market JSONB,
  economics JSONB,
  risks JSONB,
  confidence_score FLOAT DEFAULT 0,
  overall_score FLOAT,
  source_signals JSONB DEFAULT '[]',
  related_hypotheses JSONB DEFAULT '[]',
  resurrection_triggers JSONB DEFAULT '[]',
  war_room_active BOOLEAN DEFAULT false,
  auto_confirm_override BOOLEAN,
  last_evaluated_at TIMESTAMPTZ,
  tags JSONB DEFAULT '[]',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_hypotheses_domain ON hypotheses(domain);
CREATE INDEX IF NOT EXISTS ix_hypotheses_status ON hypotheses(status);

-- ── signals ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS signals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
  hypothesis_id UUID REFERENCES hypotheses(id) ON DELETE SET NULL,
  domain VARCHAR(50) NOT NULL DEFAULT 'lkm',
  title VARCHAR(500) NOT NULL,
  summary TEXT NOT NULL,
  url VARCHAR(2000),
  source_type VARCHAR(50) NOT NULL,
  relevance_score FLOAT DEFAULT 0,
  relevance_rationale TEXT,
  raw_data JSONB,
  is_processed BOOLEAN DEFAULT false,
  is_duplicate BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_signals_source_id ON signals(source_id);
CREATE INDEX IF NOT EXISTS ix_signals_domain ON signals(domain);

-- ── hypothesis_evaluations ───────────────────────────────────
CREATE TABLE IF NOT EXISTS hypothesis_evaluations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  hypothesis_id UUID NOT NULL REFERENCES hypotheses(id) ON DELETE CASCADE,
  agent_name VARCHAR(50) NOT NULL,
  run_id UUID,
  evaluated_at TIMESTAMPTZ NOT NULL,
  snapshot JSONB NOT NULL,
  delta JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_hypothesis_evaluations_hypothesis_id ON hypothesis_evaluations(hypothesis_id);

-- ── agent_settings ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agent_settings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_name VARCHAR(50) NOT NULL UNIQUE,
  display_name VARCHAR(100) NOT NULL,
  description TEXT NOT NULL,
  model VARCHAR(100) DEFAULT 'claude-sonnet-4-6',
  temperature FLOAT DEFAULT 0.3,
  max_tokens INTEGER DEFAULT 4096,
  system_prompt TEXT NOT NULL,
  system_prompt_version INTEGER DEFAULT 1,
  allowed_tools JSONB DEFAULT '[]',
  auto_confirm BOOLEAN DEFAULT false,
  cost_limit_per_run_usd FLOAT DEFAULT 1.0,
  schedule VARCHAR(100),
  is_active BOOLEAN DEFAULT true,
  prompt_history JSONB DEFAULT '[]',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ── agent_runs ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agent_runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_name VARCHAR(50) NOT NULL,
  hypothesis_id UUID REFERENCES hypotheses(id) ON DELETE SET NULL,
  source_id UUID,
  status VARCHAR(30) DEFAULT 'running',
  started_at TIMESTAMPTZ NOT NULL,
  finished_at TIMESTAMPTZ,
  input_snapshot JSONB,
  output_snapshot JSONB,
  reasoning_chain JSONB,
  tokens_input INTEGER DEFAULT 0,
  tokens_output INTEGER DEFAULT 0,
  cost_usd FLOAT DEFAULT 0,
  error TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_agent_runs_agent_name ON agent_runs(agent_name);
CREATE INDEX IF NOT EXISTS ix_agent_runs_hypothesis_id ON agent_runs(hypothesis_id);

-- ── tools_log ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tools_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  run_id UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
  tool_name VARCHAR(100) NOT NULL,
  input JSONB NOT NULL,
  output JSONB,
  duration_ms INTEGER DEFAULT 0,
  error TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_tools_log_run_id ON tools_log(run_id);

-- ── committee_sessions ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS committee_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(300) NOT NULL,
  hypothesis_ids JSONB NOT NULL DEFAULT '[]',
  status VARCHAR(30) DEFAULT 'open',
  scheduled_at TIMESTAMPTZ,
  closed_at TIMESTAMPTZ,
  summary_markdown TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ── committee_votes ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS committee_votes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID NOT NULL REFERENCES committee_sessions(id) ON DELETE CASCADE,
  hypothesis_id UUID NOT NULL REFERENCES hypotheses(id) ON DELETE CASCADE,
  voter_id UUID,
  vote VARCHAR(30) NOT NULL,
  comment TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_committee_votes_session_id ON committee_votes(session_id);
CREATE INDEX IF NOT EXISTS ix_committee_votes_hypothesis_id ON committee_votes(hypothesis_id);

-- ── Seed: agent_settings ─────────────────────────────────────
INSERT INTO agent_settings (agent_name, display_name, description, model, temperature, system_prompt)
VALUES
  ('scout','Scout','Разведчик рынка','claude-sonnet-4-6',0.5,'You are Scout, a market intelligence agent.'),
  ('curator','Curator','Куратор гипотез','claude-sonnet-4-6',0.3,'You are Curator, a hypothesis curation agent.'),
  ('tech_analyst','TechAnalyst','Технический аналитик','claude-sonnet-4-6',0.2,'You are TechAnalyst.'),
  ('market_analyst','MarketAnalyst','Рыночный аналитик','claude-sonnet-4-6',0.3,'You are MarketAnalyst.'),
  ('economist','Economist','Экономист','claude-opus-4-7',0.2,'You are Economist.'),
  ('compliance_officer','ComplianceOfficer','Офицер комплаенса','claude-opus-4-7',0.2,'You are ComplianceOfficer.'),
  ('synthesizer','Synthesizer','Синтезатор','claude-opus-4-7',0.4,'You are Synthesizer.'),
  ('devils_advocate','DevilsAdvocate','Адвокат дьявола','claude-opus-4-7',0.7,'You are DevilsAdvocate.'),
  ('orchestrator','Orchestrator','Оркестратор','claude-sonnet-4-6',0.1,'You are Orchestrator.')
ON CONFLICT (agent_name) DO NOTHING;

-- ── Realtime: включить для ключевых таблиц ───────────────────
ALTER PUBLICATION supabase_realtime ADD TABLE hypotheses;
ALTER PUBLICATION supabase_realtime ADD TABLE agent_runs;
ALTER PUBLICATION supabase_realtime ADD TABLE signals;
