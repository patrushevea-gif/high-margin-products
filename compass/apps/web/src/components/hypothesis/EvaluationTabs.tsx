"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Hypothesis } from "@/types";
import { cn, formatDate } from "@/lib/utils";
import { Clock, ChevronDown, ChevronRight } from "lucide-react";

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

interface Evaluation {
  id: string;
  agent_name: string;
  run_id: string | null;
  evaluated_at: string;
  snapshot: Record<string, unknown>;
  delta: Record<string, unknown> | null;
}

const AGENT_COLORS: Record<string, string> = {
  scout: "#6366f1",
  curator: "#8b5cf6",
  tech_analyst: "#0ea5e9",
  market_analyst: "#10b981",
  economist: "#f59e0b",
  compliance_officer: "#ef4444",
  synthesizer: "#7c3aed",
  devils_advocate: "#dc2626",
  orchestrator: "#94a3b8",
};

function HistoryTab({ hypothesisId }: { hypothesisId: string }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  const { data: evaluations = [], isLoading } = useQuery<Evaluation[]>({
    queryKey: ["evaluations", hypothesisId],
    queryFn: () => api.get<Evaluation[]>(`/hypotheses/${hypothesisId}/evaluations`),
  });

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-12 rounded animate-pulse" style={{ background: "var(--surface)" }} />
        ))}
      </div>
    );
  }

  if (evaluations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-3">
        <Clock size={28} style={{ color: "var(--text-muted)" }} />
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          История оценок пуста — агенты ещё не запускались
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      <p className="text-xs mb-3" style={{ color: "var(--text-muted)" }}>
        {evaluations.length} снимков · от новых к старым
      </p>
      {evaluations.map((ev) => {
        const isOpen = expanded === ev.id;
        const color = AGENT_COLORS[ev.agent_name] ?? "#94a3b8";
        return (
          <div key={ev.id} className="rounded border overflow-hidden"
            style={{ borderColor: "var(--border)" }}>
            <button
              onClick={() => setExpanded(isOpen ? null : ev.id)}
              className="w-full flex items-center gap-3 px-3 py-2.5 text-left hover:bg-white/5 transition-colors"
            >
              <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: color }} />
              <span className="text-xs font-medium flex-1" style={{ color: "var(--text-primary)" }}>
                {ev.agent_name}
              </span>
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                {formatDate(ev.evaluated_at)}
              </span>
              {isOpen ? <ChevronDown size={13} style={{ color: "var(--text-muted)" }} />
                       : <ChevronRight size={13} style={{ color: "var(--text-muted)" }} />}
            </button>
            {isOpen && (
              <div className="border-t px-3 py-2" style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
                {ev.delta && Object.keys(ev.delta).length > 0 && (
                  <div className="mb-2">
                    <p className="text-xs font-medium mb-1" style={{ color: "var(--text-muted)" }}>Дельта изменений</p>
                    <pre className="text-xs p-2 rounded" style={{ background: "var(--background)", color: "#10b981", fontFamily: "monospace" }}>
                      {JSON.stringify(ev.delta, null, 2)}
                    </pre>
                  </div>
                )}
                <p className="text-xs font-medium mb-1" style={{ color: "var(--text-muted)" }}>Снимок</p>
                <pre className="text-xs p-2 rounded overflow-auto max-h-64"
                  style={{ background: "var(--background)", color: "var(--text-secondary)", fontFamily: "monospace" }}>
                  {JSON.stringify(ev.snapshot, null, 2)}
                </pre>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
