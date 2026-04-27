"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Source } from "@/types";
import { formatDate, cn } from "@/lib/utils";
import { toast } from "sonner";
import { Play, Pause, Zap, CheckCircle, XCircle, Clock } from "lucide-react";

const SOURCE_TYPE_LABELS: Record<string, string> = {
  patents: "Патенты",
  scientific: "Научные",
  news: "Новости",
  competitors: "Конкуренты",
  raw_materials: "Сырьё",
  standards: "Стандарты",
  trends: "Тренды",
};

const STRATEGY_LABELS: Record<string, string> = {
  ai: "AI-парсер",
  rss: "RSS",
  api: "API",
};

export function SourcesManager() {
  const qc = useQueryClient();

  const { data: sources = [], isLoading } = useQuery<Source[]>({
    queryKey: ["sources"],
    queryFn: () => api.get<Source[]>("/sources"),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      api.patch(`/sources/${id}`, { is_active: active }),
    onSuccess: () => {
      toast.success("Источник обновлён");
      qc.invalidateQueries({ queryKey: ["sources"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const triggerMutation = useMutation({
    mutationFn: (id: string) => api.post(`/sources/${id}/trigger`, {}),
    onSuccess: () => toast.success("Парсинг запущен"),
    onError: (e: Error) => toast.error(e.message),
  });

  const byType = sources.reduce<Record<string, Source[]>>((acc, s) => {
    (acc[s.source_type] ??= []).push(s);
    return acc;
  }, {});

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div
        className="px-5 py-3 border-b"
        style={{ borderColor: "var(--border)", background: "var(--surface)" }}
      >
        <h1 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          Источники данных
        </h1>
        <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
          {sources.filter((s) => s.is_active).length} активных из {sources.length}
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-5 space-y-6">
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-12 rounded animate-pulse" style={{ background: "var(--surface)" }} />
            ))}
          </div>
        ) : (
          Object.entries(byType).map(([type, srcs]) => (
            <div key={type}>
              <h2 className="text-xs font-semibold uppercase tracking-wider mb-2"
                style={{ color: "var(--accent)" }}>
                {SOURCE_TYPE_LABELS[type] ?? type}
              </h2>
              <div className="space-y-1.5">
                {srcs.map((src) => (
                  <SourceCard
                    key={src.id}
                    source={src}
                    onToggle={(active) => toggleMutation.mutate({ id: src.id, active })}
                    onTrigger={() => triggerMutation.mutate(src.id)}
                  />
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function SourceCard({
  source: s,
  onToggle,
  onTrigger,
}: {
  source: Source;
  onToggle: (active: boolean) => void;
  onTrigger: () => void;
}) {
  return (
    <div
      className="flex items-center gap-3 px-3 py-2.5 rounded border"
      style={{
        borderColor: "var(--border)",
        background: "var(--surface)",
        opacity: s.is_active ? 1 : 0.5,
      }}
    >
      {/* Status indicator */}
      <div className="flex-shrink-0">
        {s.last_run_success === true ? (
          <CheckCircle size={14} style={{ color: "var(--success)" }} />
        ) : s.last_run_success === false ? (
          <XCircle size={14} style={{ color: "var(--danger)" }} />
        ) : (
          <Clock size={14} style={{ color: "var(--text-muted)" }} />
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium truncate" style={{ color: "var(--text-primary)" }}>
            {s.name}
          </span>
          <span
            className="text-xs px-1.5 py-0.5 rounded flex-shrink-0"
            style={{ background: "var(--raised)", color: "var(--text-muted)" }}
          >
            {STRATEGY_LABELS[s.parsing_strategy] ?? s.parsing_strategy}
          </span>
          {s.prefer_api && (
            <span className="text-xs" style={{ color: "var(--success)" }}>API</span>
          )}
        </div>
        <div className="flex items-center gap-3 text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
          <span>{s.schedule}</span>
          {s.last_run_at && <span>Последний: {formatDate(s.last_run_at)}</span>}
          {s.last_run_signals > 0 && <span>{s.last_run_signals} сигналов</span>}
          {s.cost_usd_month > 0 && <span>${s.cost_usd_month.toFixed(3)}/мес</span>}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1.5 flex-shrink-0">
        <button
          onClick={onTrigger}
          className="p-1.5 rounded hover:bg-background-raised transition-colors"
          title="Запустить сейчас"
          style={{ color: "var(--accent)" }}
        >
          <Zap size={13} />
        </button>
        <button
          onClick={() => onToggle(!s.is_active)}
          className="p-1.5 rounded hover:bg-background-raised transition-colors"
          title={s.is_active ? "Приостановить" : "Активировать"}
          style={{ color: s.is_active ? "var(--success)" : "var(--text-muted)" }}
        >
          {s.is_active ? <Pause size={13} /> : <Play size={13} />}
        </button>
      </div>
    </div>
  );
}
