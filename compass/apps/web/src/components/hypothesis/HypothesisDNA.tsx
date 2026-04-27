"use client";

import { Hypothesis } from "@/types";

interface Props {
  hypothesis: Hypothesis;
}

function DNARow({ label, value }: { label: string; value: string | number | undefined | null }) {
  return (
    <div className="flex items-start justify-between gap-2 py-1.5 border-b text-xs"
      style={{ borderColor: "var(--border)" }}>
      <span style={{ color: "var(--text-muted)" }}>{label}</span>
      <span className="text-right font-medium" style={{ color: "var(--text-primary)" }}>
        {value ?? "—"}
      </span>
    </div>
  );
}

export function HypothesisDNA({ hypothesis: h }: Props) {
  const t = h.technical ?? {};
  const m = h.market ?? {};
  const e = h.economics ?? {};
  const r = h.risks ?? {};

  return (
    <div className="p-3">
      <p className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>
        Hypothesis DNA
      </p>

      <div className="mb-3">
        <p className="text-xs uppercase tracking-wider mb-1" style={{ color: "var(--accent)" }}>
          Технико
        </p>
        <DNARow label="Сложность" value={t.complexity != null ? `${t.complexity}/5` : null} />
        <DNARow label="Оборудование" value={t.equipment_modification} />
        <DNARow label="Сырьё" value={t.raw_material_availability} />
        <DNARow label="TRL" value={t.trl != null ? `${t.trl}/9` : null} />
      </div>

      <div className="mb-3">
        <p className="text-xs uppercase tracking-wider mb-1" style={{ color: "var(--accent)" }}>
          Рынок
        </p>
        <DNARow label="Размер рынка" value={m.market_size_mln_rub != null ? `${m.market_size_mln_rub} млн ₽` : null} />
        <DNARow label="CAGR" value={m.cagr_pct != null ? `${m.cagr_pct}%` : null} />
        <DNARow label="Конкуренция" value={m.competitive_density} />
      </div>

      <div className="mb-3">
        <p className="text-xs uppercase tracking-wider mb-1" style={{ color: "var(--accent)" }}>
          Экономика
        </p>
        <DNARow label="Маржа" value={e.margin_pct != null ? `${e.margin_pct}%` : null} />
        <DNARow label="Маржа ₽/ед" value={e.margin_rub_per_unit} />
        <DNARow label="Окупаемость" value={e.roi_months != null ? `${e.roi_months} мес` : null} />
      </div>

      <div className="mb-3">
        <p className="text-xs uppercase tracking-wider mb-1" style={{ color: "var(--accent)" }}>
          Риски
        </p>
        <DNARow label="Риск-скор" value={r.overall_risk_score != null ? `${r.overall_risk_score}/10` : null} />
        <DNARow label="Патентный" value={r.patent_risk != null ? `${Math.round(r.patent_risk * 100)}%` : null} />
        <DNARow label="Регуляторный" value={r.regulatory_risk != null ? `${Math.round(r.regulatory_risk * 100)}%` : null} />
      </div>

      <div>
        <p className="text-xs uppercase tracking-wider mb-1" style={{ color: "var(--accent)" }}>
          Уверенность
        </p>
        <div className="relative h-2 rounded-full overflow-hidden" style={{ background: "var(--raised)" }}>
          <div
            className="absolute left-0 top-0 h-full rounded-full transition-all"
            style={{
              width: `${Math.round(h.confidence_score * 100)}%`,
              background: "var(--accent)",
            }}
          />
        </div>
        <p className="text-xs mt-1 text-right" style={{ color: "var(--text-muted)" }}>
          {Math.round(h.confidence_score * 100)}%
        </p>
      </div>
    </div>
  );
}
