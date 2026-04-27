"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Hypothesis } from "@/types";
import { cn, STATUS_LABELS, DOMAIN_LABELS } from "@/lib/utils";
import { toast } from "sonner";
import { GitCompareArrows } from "lucide-react";

interface CompareRow {
  label: string;
  getValue: (h: Hypothesis) => string | number | undefined | null;
  format?: (v: any) => string;
  highlight?: boolean;
}

const ROWS: CompareRow[] = [
  { label: "Домен", getValue: (h) => DOMAIN_LABELS[h.domain] ?? h.domain },
  { label: "Статус", getValue: (h) => STATUS_LABELS[h.status] ?? h.status },
  { label: "Итоговая оценка", getValue: (h) => h.overall_score, format: (v) => v != null ? `${v.toFixed(1)}/10` : "—", highlight: true },
  { label: "Уверенность", getValue: (h) => h.confidence_score, format: (v) => `${Math.round(v * 100)}%` },
  // Technical
  { label: "Сложность (техника)", getValue: (h) => (h.technical as any)?.complexity, format: (v) => v != null ? `${v}/5` : "—" },
  { label: "Оборудование", getValue: (h) => (h.technical as any)?.equipment_modification ?? "—" },
  { label: "TRL", getValue: (h) => (h.technical as any)?.trl, format: (v) => v != null ? `${v}/9` : "—" },
  // Market
  { label: "Рынок (млн ₽)", getValue: (h) => (h.market as any)?.market_size_mln_rub, format: (v) => v != null ? `${v} млн` : "—" },
  { label: "CAGR", getValue: (h) => (h.market as any)?.cagr_pct, format: (v) => v != null ? `${v}%` : "—" },
  { label: "Конкуренция", getValue: (h) => (h.market as any)?.competitive_density ?? "—" },
  // Economics
  { label: "Маржа %", getValue: (h) => (h.economics as any)?.margin_pct, format: (v) => v != null ? `${v}%` : "—", highlight: true },
  { label: "Окупаемость", getValue: (h) => (h.economics as any)?.roi_months, format: (v) => v != null ? `${v} мес` : "—" },
  // Risks
  { label: "Риск-скор", getValue: (h) => (h.risks as any)?.overall_risk_score, format: (v) => v != null ? `${v}/10` : "—", highlight: true },
  { label: "Патентный риск", getValue: (h) => (h.risks as any)?.patent_risk, format: (v) => v != null ? `${Math.round(v * 100)}%` : "—" },
  { label: "Регуляторный риск", getValue: (h) => (h.risks as any)?.regulatory_risk, format: (v) => v != null ? `${Math.round(v * 100)}%` : "—" },
  { label: "War Room", getValue: (h) => h.war_room_active ? "Да" : "Нет" },
];

function cellColor(row: CompareRow, value: any, allValues: any[]): string {
  if (!row.highlight || value == null) return "";
  const nums = allValues.filter((v) => v != null && typeof v === "number") as number[];
  if (nums.length < 2) return "";
  const max = Math.max(...nums);
  const min = Math.min(...nums);
  if (max === min) return "";
  // For risk: lower = better (green)
  const isRisk = row.label.toLowerCase().includes("риск");
  const isBest = isRisk ? value === min : value === max;
  const isWorst = isRisk ? value === max : value === min;
  if (isBest) return "rgba(16, 185, 129, 0.12)";
  if (isWorst) return "rgba(239, 68, 68, 0.10)";
  return "";
}

export function HypothesisCompare() {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [summary, setSummary] = useState<string | null>(null);

  const { data: hypotheses = [] } = useQuery<Hypothesis[]>({
    queryKey: ["hypotheses"],
    queryFn: () => api.get<Hypothesis[]>("/hypotheses?limit=200"),
  });

  const comparables = hypotheses.filter((h) => selectedIds.has(h.id));

  const summaryMutation = useMutation({
    mutationFn: () =>
      api.post<{ text: string }>("/counterfactual/analyze", {
        hypothesis_ids: Array.from(selectedIds),
        scenario: { name: "compare_summary", changes: [] },
      }),
    onSuccess: () => setSummary("Синтетический сравнительный анализ будет добавлен в следующей итерации."),
    onError: () => setSummary("Синтетическое сравнение — в разработке."),
  });

  const toggle = (id: string) => {
    const next = new Set(selectedIds);
    if (next.has(id)) {
      next.delete(id);
    } else if (next.size < 5) {
      next.add(id);
    } else {
      toast.warning("Максимум 5 гипотез для сравнения");
    }
    setSelectedIds(next);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b"
        style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
        <div>
          <h1 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Сравнение гипотез
          </h1>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
            Выберите 2–5 гипотез для сравнения
          </p>
        </div>
        {comparables.length >= 2 && (
          <button
            onClick={() => summaryMutation.mutate()}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm"
            style={{ background: "var(--accent)", color: "white" }}
          >
            <GitCompareArrows size={13} /> Agentic Summary
          </button>
        )}
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left: picker */}
        <div className="w-64 flex-shrink-0 border-r overflow-auto"
          style={{ borderColor: "var(--border)" }}>
          <div className="px-3 py-2 text-xs font-medium border-b"
            style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}>
            Список гипотез
          </div>
          {hypotheses.map((h) => (
            <label key={h.id}
              className="flex items-start gap-2 px-3 py-2 border-b cursor-pointer hover:bg-background-raised transition-colors"
              style={{ borderColor: "var(--border)" }}>
              <input
                type="checkbox"
                checked={selectedIds.has(h.id)}
                onChange={() => toggle(h.id)}
                className="mt-0.5 accent-purple-600"
              />
              <div>
                <p className="text-xs font-medium leading-snug" style={{ color: "var(--text-primary)" }}>
                  {h.title}
                </p>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {STATUS_LABELS[h.status] ?? h.status}
                  {h.overall_score != null && ` · ${h.overall_score.toFixed(1)}`}
                </p>
              </div>
            </label>
          ))}
        </div>

        {/* Right: comparison matrix */}
        <div className="flex-1 overflow-auto">
          {comparables.length < 2 ? (
            <div className="flex items-center justify-center h-full text-sm"
              style={{ color: "var(--text-muted)" }}>
              Выберите минимум 2 гипотезы слева
            </div>
          ) : (
            <div>
              {summary && (
                <div className="m-4 p-3 rounded border text-sm"
                  style={{ borderColor: "var(--accent)", background: "rgba(124,58,237,0.06)", color: "var(--text-secondary)" }}>
                  {summary}
                </div>
              )}
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr style={{ background: "var(--surface)", borderBottom: "1px solid var(--border)" }}>
                    <th className="text-left px-4 py-2.5 font-medium w-40" style={{ color: "var(--text-muted)" }}>
                      Метрика
                    </th>
                    {comparables.map((h) => (
                      <th key={h.id} className="text-left px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>
                        <span className="line-clamp-2">{h.title}</span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {ROWS.map((row) => {
                    const values = comparables.map((h) => row.getValue(h));
                    return (
                      <tr key={row.label} className="border-b"
                        style={{ borderColor: "var(--border)" }}>
                        <td className="px-4 py-2 font-medium" style={{ color: "var(--text-muted)" }}>
                          {row.label}
                        </td>
                        {comparables.map((h, i) => {
                          const raw = values[i];
                          const display = row.format ? row.format(raw) : (raw ?? "—");
                          const bg = cellColor(row, typeof raw === "number" ? raw : null, values.map(v => typeof v === "number" ? v : null));
                          return (
                            <td key={h.id} className="px-4 py-2"
                              style={{ color: "var(--text-primary)", background: bg }}>
                              {String(display)}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
