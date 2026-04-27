export type HypothesisStatus =
  | "draft" | "signal_processed" | "tech_evaluated" | "market_evaluated"
  | "economics_evaluated" | "compliance_checked" | "synthesized"
  | "challenged" | "committee_ready" | "committee_decision"
  | "accepted" | "rejected" | "parked" | "to_review";

export type Domain =
  | "lkm" | "soj" | "lubricants" | "anticor" | "sealants"
  | "adhesives" | "specialty" | "reagents" | "additives" | "surfactants";

export interface TechnicalProfile {
  complexity?: number;
  equipment_modification?: "none" | "minor" | "major" | "new";
  raw_material_availability?: "available" | "partial" | "closed";
  trl?: number;
  notes?: string;
}

export interface MarketProfile {
  market_size_mln_rub?: number;
  cagr_pct?: number;
  competitive_density?: "low" | "medium" | "high";
  target_segments?: string[];
  geographic_focus?: string[];
  notes?: string;
}

export interface EconomicsProfile {
  cost_per_unit_rub?: number;
  price_per_unit_rub?: number;
  margin_pct?: number;
  margin_rub_per_unit?: number;
  min_batch_units?: number;
  roi_months?: number;
  notes?: string;
}

export interface RisksProfile {
  overall_risk_score?: number;
  patent_risk?: number;
  regulatory_risk?: number;
  raw_material_volatility_risk?: number;
  technology_risk?: number;
  notes?: string;
}

export interface Hypothesis {
  id: string;
  title: string;
  short_description: string;
  long_description?: string;
  domain: Domain;
  status: HypothesisStatus;
  curator_id?: string;
  technical?: TechnicalProfile;
  market?: MarketProfile;
  economics?: EconomicsProfile;
  risks?: RisksProfile;
  confidence_score: number;
  overall_score?: number;
  source_signals: string[];
  related_hypotheses: string[];
  war_room_active: boolean;
  tags: string[];
  created_at: string;
  updated_at: string;
  last_evaluated_at?: string;
}

export interface Signal {
  id: string;
  source_id?: string;
  hypothesis_id?: string;
  domain: Domain;
  title: string;
  summary: string;
  url?: string;
  source_type: string;
  relevance_score: number;
  relevance_rationale?: string;
  is_processed: boolean;
  is_duplicate: boolean;
  created_at: string;
  updated_at: string;
}

export interface Source {
  id: string;
  name: string;
  url_pattern?: string;
  source_type: string;
  domain: string;
  parsing_strategy: "ai" | "rss" | "api";
  rate_limit_rpm: number;
  api_endpoint?: string;
  prefer_api: boolean;
  schedule: string;
  is_active: boolean;
  last_run_at?: string;
  last_run_success?: boolean;
  last_run_signals: number;
  tokens_used_month: number;
  cost_usd_month: number;
  created_at: string;
  updated_at: string;
}

export interface AgentSettings {
  id: string;
  agent_name: string;
  display_name: string;
  description: string;
  model: string;
  temperature: number;
  max_tokens: number;
  system_prompt: string;
  system_prompt_version: number;
  allowed_tools: string[];
  auto_confirm: boolean;
  cost_limit_per_run_usd: number;
  schedule?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
