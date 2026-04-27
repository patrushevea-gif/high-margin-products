"use client";

import { useState } from "react";
import { Hypothesis } from "@/types";
import { cn } from "@/lib/utils";

const TABS = [
  { id: "summary", label: "Сводка" },
  { id: "tech", label: "Технико" },
  { id: "market", label: "Рынок" },
  { id: "economics", label: "Экономика" },
  { id: "risks", label: "Риски" },
  { id: "history", label: "История" },
];

interface Props {
  hypothesis: Hypothesis;
}

export function EvaluationTabs({ hypothesis: h }: Props) {
  const [active, setActive] = useState("summary");

  return (
    <div className="flex flex-col h-full">
      {/* Tab bar */}
      <div
        className="flex gap-1 px-4 pt-3 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActive(tab.id)}
            className={cn(
              "px-3 py-2 text-xs border-b-2 transition-colors",
              active === tab.id
                ? "border-accent font-medium"
                : "border-transparent hover:border-border"
            )}
            style={{
              color: active === tab.id ? "var(--accent)" : "var(--text-muted)",
              borderColor: active === tab.id ? "var(--accent)" : "transparent",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {active === "summary" && <SummaryTab h={h} />}
        {active === "tech" && <JSONTab data={h.technical} label="Технический анализ" />}
        {active === "market" && <JSONTab data={h.market} label="Рыночный анализ" />}
        {active === "economics" && <JSONTab data={h.economics} label="Экономика" />}
        {active === "risks" && <JSONTab data={h.risks} label="Риски" />}
        {active === "history" && <HistoryTab hypothesisId={h.id} />}
      </div>
    </div>
  );
}

function SummaryTab({ h }: { h: Hypothesis }) {
  return (
    <div className="space-y-4 max-w-2xl">
      <div>
        <h3 className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>Описание</h3>
        <p className="text-sm leading-relaxed" style={{ color: "var(--text-primary)" }}>
          {h.long_description || h.short_description}
        </p>
      </div>
      {h.tags.length > 0 && (
        <div>
          <h3 className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>Теги</h3>
          <div className="flex flex-wrap gap-1.5">
            {h.tags.map((tag) => (
              <span key={tag} className="text-xs px-2 py-0.5 rounded"
                style={{ background: "var(--raised)", color: "var(--text-secondary)" }}>
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}
      {h.overall_score != null && (
        <div>
          <h3 className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>
            Итоговая оценка
          </h3>
          <div className="text-2xl font-semibold" style={{ color: "var(--accent)" }}>
            {h.overall_score.toFixed(1)} / 10
          </div>
        </div>
      )}
    </div>
  );
}

function JSONTab({ data, label }: { data: object | null | undefined; label: string }) {
  if (!data) {
    return (
      <div className="text-sm" style={{ color: "var(--text-muted)" }}>
        Данные ещё не получены. Запустите оценку.
      </div>
    );
  }
  return (
    <div>
      <h3 className="text-xs font-medium mb-3" style={{ color: "var(--text-muted)" }}>{label}</h3>
      <pre
        className="text-xs p-3 rounded overflow-auto"
        style={{
          background: "var(--surface)",
          color: "var(--text-secondary)",
          fontFamily: "JetBrains Mono, monospace",
          border: "1px solid var(--border)",
        }}
      >
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}

function HistoryTab({ hypothesisId }: { hypothesisId: string }) {
  return (
    <div className="text-sm" style={{ color: "var(--text-muted)" }}>
      История оценок (Time Machine) — появится по мере прохождения агентов.
    </div>
  );
}
