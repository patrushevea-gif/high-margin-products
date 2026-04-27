"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Hypothesis } from "@/types";
import { STATUS_LABELS, STATUS_COLORS, DOMAIN_LABELS, formatDate, cn } from "@/lib/utils";
import { toast } from "sonner";
import { Zap, RefreshCw, ArrowRight, Archive, Check } from "lucide-react";
import { HypothesisDNA } from "./HypothesisDNA";
import { EvaluationTabs } from "./EvaluationTabs";

interface Props {
  id: string;
}

export function HypothesisWorkbench({ id }: Props) {
  const qc = useQueryClient();

  const { data: h, isLoading } = useQuery<Hypothesis>({
    queryKey: ["hypothesis", id],
    queryFn: () => api.get<Hypothesis>(`/hypotheses/${id}`),
  });

  const advanceMutation = useMutation({
    mutationFn: () => api.post(`/hypotheses/${id}/advance`, {}),
    onSuccess: () => {
      toast.success("Гипотеза передана на следующий этап");
      qc.invalidateQueries({ queryKey: ["hypothesis", id] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const warRoomMutation = useMutation({
    mutationFn: (active: boolean) =>
      api.patch(`/hypotheses/${id}`, { war_room_active: active }),
    onSuccess: () => {
      toast.success("Статус War Room обновлён");
      qc.invalidateQueries({ queryKey: ["hypothesis", id] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: () => api.patch(`/hypotheses/${id}`, { status: "rejected" }),
    onSuccess: () => {
      toast.success("Гипотеза отвергнута");
      qc.invalidateQueries({ queryKey: ["hypothesis", id] });
    },
  });

  if (isLoading) {
    return (
      <div className="p-6 space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-10 rounded animate-pulse" style={{ background: "var(--surface)" }} />
        ))}
      </div>
    );
  }

  if (!h) return <div className="p-6" style={{ color: "var(--text-muted)" }}>Гипотеза не найдена</div>;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div
        className="px-5 py-3 border-b"
        style={{ borderColor: "var(--border)", background: "var(--surface)" }}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                {DOMAIN_LABELS[h.domain] ?? h.domain}
              </span>
              <span className="text-xs">·</span>
              <span className={cn("text-xs", STATUS_COLORS[h.status])}>
                {STATUS_LABELS[h.status] ?? h.status}
              </span>
              {h.war_room_active && (
                <span className="text-xs px-1.5 py-0.5 rounded animate-pulse"
                  style={{ background: "rgba(239,68,68,0.15)", color: "var(--danger)" }}>
                  WAR ROOM
                </span>
              )}
            </div>
            <h1 className="text-base font-semibold leading-snug" style={{ color: "var(--text-primary)" }}>
              {h.title}
            </h1>
            <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
              {h.short_description}
            </p>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={() => warRoomMutation.mutate(!h.war_room_active)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm border transition-colors"
              style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
            >
              <Zap size={13} />
              {h.war_room_active ? "Снять War Room" : "War Room"}
            </button>
            <button
              onClick={() => rejectMutation.mutate()}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm border transition-colors"
              style={{ borderColor: "var(--border)", color: "var(--danger)" }}
            >
              <Archive size={13} /> Отвергнуть
            </button>
            <button
              onClick={() => advanceMutation.mutate()}
              disabled={advanceMutation.isPending}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm"
              style={{ background: "var(--accent)", color: "white" }}
            >
              <ArrowRight size={13} /> Продвинуть
            </button>
          </div>
        </div>

        <div className="flex items-center gap-4 mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
          <span>Создана: {formatDate(h.created_at)}</span>
          {h.last_evaluated_at && <span>Оценка: {formatDate(h.last_evaluated_at)}</span>}
          {h.confidence_score > 0 && <span>Уверенность: {Math.round(h.confidence_score * 100)}%</span>}
          {h.overall_score != null && <span>Оценка: {h.overall_score.toFixed(1)}/10</span>}
        </div>
      </div>

      {/* Body: 3 columns */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: DNA */}
        <div
          className="w-60 flex-shrink-0 border-r overflow-auto"
          style={{ borderColor: "var(--border)" }}
        >
          <HypothesisDNA hypothesis={h} />
        </div>

        {/* Center: tabs */}
        <div className="flex-1 overflow-auto">
          <EvaluationTabs hypothesis={h} />
        </div>
      </div>
    </div>
  );
}
