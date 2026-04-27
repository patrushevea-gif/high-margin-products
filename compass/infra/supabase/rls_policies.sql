-- Row Level Security policies for Compass
-- Enable RLS on all tables

ALTER TABLE hypotheses ENABLE ROW LEVEL SECURITY;
ALTER TABLE signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE hypothesis_evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE tools_log ENABLE ROW LEVEL SECURITY;

-- Helper: get role from JWT metadata
CREATE OR REPLACE FUNCTION auth_role() RETURNS text AS $$
  SELECT COALESCE(
    (auth.jwt() -> 'user_metadata' ->> 'role'),
    'viewer'
  );
$$ LANGUAGE sql STABLE;

-- Hypotheses: all authenticated users can read, researchers+ can write
CREATE POLICY "hypotheses_select" ON hypotheses
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "hypotheses_insert" ON hypotheses
  FOR INSERT TO authenticated
  WITH CHECK (auth_role() IN ('researcher', 'admin'));

CREATE POLICY "hypotheses_update" ON hypotheses
  FOR UPDATE TO authenticated
  USING (
    auth_role() IN ('researcher', 'admin') OR
    curator_id = auth.uid()
  );

-- Signals: read-only for most roles
CREATE POLICY "signals_select" ON signals
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "signals_insert" ON signals
  FOR INSERT TO authenticated
  WITH CHECK (auth_role() IN ('researcher', 'admin'));

-- Sources: admin-only write
CREATE POLICY "sources_select" ON sources
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "sources_write" ON sources
  FOR ALL TO authenticated
  USING (auth_role() = 'admin')
  WITH CHECK (auth_role() = 'admin');

-- Agent settings: admin-only write
CREATE POLICY "agent_settings_select" ON agent_settings
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "agent_settings_write" ON agent_settings
  FOR ALL TO authenticated
  USING (auth_role() = 'admin')
  WITH CHECK (auth_role() = 'admin');

-- Agent runs: read-only for authenticated
CREATE POLICY "agent_runs_select" ON agent_runs
  FOR SELECT TO authenticated USING (true);

-- Evaluations: read-only
CREATE POLICY "evaluations_select" ON hypothesis_evaluations
  FOR SELECT TO authenticated USING (true);

-- Tools log: read-only for researchers+
CREATE POLICY "tools_log_select" ON tools_log
  FOR SELECT TO authenticated
  USING (auth_role() IN ('researcher', 'admin', 'technologist'));
