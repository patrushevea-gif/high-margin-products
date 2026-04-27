"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Hypothesis } from "@/types";
import { DOMAIN_LABELS, STATUS_LABELS, cn } from "@/lib/utils";
import { toast } from "sonner";
import { Plus, Trash2, FlaskConical, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface Change {
  type: string;
  target: string;
  operator: string;
  value: string;
  unit: string;
}

interface CFResult {
  hypothesis_id: string;
  title: string;
  original_status: string;
  original_score: number | null;
  scenario_score: number | null;
  delta: number | null;
  flip: boolean;
  explanation: string;
}

const CHANGE_TYPES = ["price_change", "regulation_change", "patent_expiry", "cost_reduction", "demand_shift", "technology_leap"];
const OPERATORS = ["increase", "decrease", "set_to", "remove"];

const emptyChange = (): Change => ({ type: "price_change", target: "", operator: "increase", value: "20", unit: "%" });

export function CounterfactualEngine() {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [scenarioName, setScenarioName] = useState("Новый сценарий");
  const [changes, setChanges] = useState<Change[]>([emptyChange()]);
  const [results, setResults] = useState<CFResult[] | null>(null);

  const { data: hypotheses = [] } = useQuery<Hypothesis[]>({
    queryKey: ["hypotheses"],
    queryFn: () => api.get<Hypothesis[]>("/hypotheses?limit=200"),
  });

  const mutation = useMutation({
    mutationFn: () =>
      api.post<CFResult[]>("/counterfactual/analyze", {
        hypothesis_ids: Array.from(selectedIds),
        scenario: { name: scenarioName, changes },
        include_rejected: true,
      }),
    onSuccess: (data) => { setResults(data); toast.success("Анализ завершён"); },
    onError: () => toast.error("Ошибка анализа"),
  });

  const toggle = (id: string) => {
    const next = new Set(selectedIds);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelectedIds(next);
  };

  const addChange = () => setChanges((c) => [...c, emptyChange()]);
  const removeChange = (i: number) => setChanges((c) => c.filter((_, idx) => idx !== i));
  const setChange = (i: number, k: keyof Change, v: string) =>
    setChanges((c) => c.map((ch, idx) => (idx === i ? { ...ch, [k]: v } : ch)));

  const canRun = selectedIds.size > 0 && scenarioName.trim() && changes.length > 0;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b"
        style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
        <div>
          <h1 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Контрфактический движок
          </h1>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
            «А что если...» — оценка гипотез при изменении условий
          </p>
        </div>
        <button
          disabled={!canRun || mutation.isPending}
          onClick={() => mutation.mutate()}
          className="flex items-center gap-2 px-4 py-2 rounded text-sm font-medium disabled:opacity-40 transition-colors"
          style={{ background: "var(--accent)", color: "white" }}
        >
          <FlaskConical size={14} />
          {mutation.isPending ? "Анализ..." : "Запустить"}
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left: hypothesis picker */}
        <div className="w-60 flex-shrink-0 border-r overflow-auto"
          style={{ borderColor: "var(--border)" }}>
          <div className="px-3 py-2 text-xs font-medium border-b"
            style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}>
            Гипотезы ({selectedIds.size} выбрано)
          </div>
          {hypotheses.map((h) => (
            <label key={h.id}
              className="flex items-start gap-2 px-3 py-2 border-b cursor-pointer hover:bg-white/5 transition-colors"
              style={{ borderColor: "var(--border)" }}>
              <input
                type="checkbox"
                checked={selectedIds.has(h.id)}
                onChange={() => toggle(h.id)}
                className="mt-0.5 accent-purple-600"
              />
              <div className="min-w-0">
                <p className="text-xs font-medium leading-snug truncate" style={{ color: "var(--text-primary)" }}>
                  {h.title}
                </p>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {DOMAIN_LABELS[h.domain] ?? h.domain} · {STATUS_LABELS[h.status] ?? h.status}
                </p>
              </div>
            </label>
          ))}
        </div>

        {/* Center: scenario builder */}
        <div className="w-80 flex-shrink-0 border-r overflow-auto p-4 space-y-4"
          style={{ borderColor: "var(--border)" }}>
          <div>
            <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-muted)" }}>
              Название сценария
            </label>
            <input
              value={scenarioName}
              onChange={(e) => setScenarioName(e.target.value)}
              className="w-full px-2.5 py-1.5 rounded text-xs border outline-none focus:border-purple-500"
              style={{ background: "var(--background)", borderColor: "var(--border)", color: "var(--text-primary)" }}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>
                Изменения условий
              </span>
              <button onClick={addChange}
                className="flex items-center gap-1 text-xs px-2 py-1 rounded transition-colors"
                style={{ color: "var(--accent)", background: "rgba(124,58,237,0.1)" }}>
                <Plus size={11} /> Добавить
              </button>
            </div>

            <div className="space-y-3">
              {changes.map((ch, i) => (
                <div key={i} className="p-3 rounded border space-y-2"
                  style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                      Изменение {i + 1}
                    </span>
                    {changes.length > 1 && (
                      <button onClick={() => removeChange(i)}>
                        <Trash2 size={12} style={{ color: "var(--text-muted)" }} />
                      </button>
                    )}
                  </div>
                  <select value={ch.type} onChange={(e) => setChange(i, "type", e.target.value)}
                    className="w-full px-2 py-1.5 rounded text-xs border"
                    style={{ background: "var(--background)", borderColor: "var(--border)", color: "var(--text-primary)" }}>
                    {CHANGE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                  <input value={ch.target} onChange={(e) => setChange(i, "target", e.target.value)}
                    placeholder="Объект (напр. сырьё, конкурент)"
                    className="w-full px-2 py-1.5 rounded text-xs border"
                    style={{ background: "var(--background)", borderColor: "var(--border)", color: "var(--text-primary)" }} />
                  <div className="flex gap-2">
                    <select value={ch.operator} onChange={(e) => setChange(i, "operator", e.target.value)}
                      className="flex-1 px-2 py-1.5 rounded text-xs border"
                      style={{ background: "var(--background)", borderColor: "var(--border)", color: "var(--text-primary)" }}>
                      {OPERATORS.map((o) => <option key={o} value={o}>{o}</option>)}
                    </select>
                    <input value={ch.value} onChange={(e) => setChange(i, "value", e.target.value)}
                      placeholder="Значение"
                      className="w-20 px-2 py-1.5 rounded text-xs border"
                      style={{ background: "var(--background)", borderColor: "var(--border)", color: "var(--text-primary)" }} />
                    <input value={ch.unit} onChange={(e) => setChange(i, "unit", e.target.value)}
                      placeholder="Ед."
                      className="w-14 px-2 py-1.5 rounded text-xs border"
                      style={{ background: "var(--background)", borderColor: "var(--border)", color: "var(--text-primary)" }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: results */}
        <div className="flex-1 overflow-auto p-4">
          {!results ? (
            <div className="flex flex-col items-center justify-center h-full gap-3">
              <FlaskConical size={32} style={{ color: "var(--text-muted)" }} />
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                Выберите гипотезы, настройте сценарий и нажмите «Запустить»
              </p>
            </div>
          ) : (
            <div className="space-y-3 max-w-2xl">
              <h2 className="text-xs font-medium mb-3" style={{ color: "var(--text-muted)" }}>
                Результаты: {results.length} гипотез проанализировано
              </h2>
              {results.map((r) => (
                <ResultCard key={r.hypothesis_id} result={r} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ResultCard({ result: r }: { result: CFResult }) {
  const hasDelta = r.delta != null;
  const up = hasDelta && r.delta! > 0;
  const down = hasDelta && r.delta! < 0;

  return (
    <div className={cn("rounded border p-4", r.flip && "ring-1 ring-purple-500")}
      style={{ borderColor: r.flip ? "var(--accent)" : "var(--border)", background: "var(--surface)" }}>
      <div className="flex items-start justify-between gap-3 mb-2">
        <p className="text-sm font-medium leading-snug" style={{ color: "var(--text-primary)" }}>
          {r.title}
        </p>
        {r.flip && (
          <span className="flex-shrink-0 text-xs px-2 py-0.5 rounded font-medium"
            style={{ background: "rgba(124,58,237,0.15)", color: "var(--accent)" }}>
            FLIP
          </span>
        )}
      </div>

      <div className="flex items-center gap-4 mb-3">
        <div className="text-xs" style={{ color: "var(--text-muted)" }}>
          Было: <span style={{ color: "var(--text-primary)" }}>{r.original_score?.toFixed(1) ?? "—"}</span>
        </div>
        <div className="text-xs" style={{ color: "var(--text-muted)" }}>
          Стало: <span style={{ color: "var(--text-primary)" }}>{r.scenario_score?.toFixed(1) ?? "—"}</span>
        </div>
        {hasDelta && (
          <div className={cn("flex items-center gap-1 text-xs font-medium")}>
            {up ? <TrendingUp size={13} style={{ color: "#10b981" }} /> :
             down ? <TrendingDown size={13} style={{ color: "#ef4444" }} /> :
             <Minus size={13} style={{ color: "var(--text-muted)" }} />}
            <span style={{ color: up ? "#10b981" : down ? "#ef4444" : "var(--text-muted)" }}>
              {up ? "+" : ""}{r.delta!.toFixed(1)}
            </span>
          </div>
        )}
      </div>

      <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
        {r.explanation}
      </p>
    </div>
  );
}
