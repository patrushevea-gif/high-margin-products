"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Hypothesis } from "@/types";
import { toast } from "sonner";
import { FileText, CheckCircle, XCircle, Clock, Users } from "lucide-react";
import { cn, formatDate } from "@/lib/utils";

const VOTES = [
  { value: "proceed", label: "Запустить пилот", icon: CheckCircle, color: "var(--success)" },
  { value: "defer", label: "Отложить", icon: Clock, color: "var(--warning)" },
  { value: "reject", label: "Отклонить", icon: XCircle, color: "var(--danger)" },
  { value: "request_data", label: "Запросить данные", icon: Users, color: "var(--info)" },
];

export function CommitteeScreen() {
  const qc = useQueryClient();
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [votingHypId, setVotingHypId] = useState<string | null>(null);
  const [voteComment, setVoteComment] = useState("");
  const [generatedReport, setGeneratedReport] = useState<string | null>(null);

  const { data: readyHyps = [] } = useQuery<Hypothesis[]>({
    queryKey: ["hypotheses", "committee_ready"],
    queryFn: () => api.get<Hypothesis[]>("/hypotheses?status=committee_ready&limit=50"),
  });

  const reportMutation = useMutation({
    mutationFn: () =>
      api.post<{ markdown: string; cost_usd: number }>("/committee/report/generate", Array.from(selectedIds)),
    onSuccess: (data) => {
      setGeneratedReport(data.markdown);
      toast.success(`Отчёт сгенерирован · $${data.cost_usd.toFixed(4)}`);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const voteMutation = useMutation({
    mutationFn: ({ hypothesisId, vote }: { hypothesisId: string; vote: string }) =>
      api.post("/committee/vote", {
        session_id: "direct",
        hypothesis_id: hypothesisId,
        voter_id: "current-user",
        vote,
        comment: voteComment,
      }),
    onSuccess: () => {
      toast.success("Голос записан");
      setVotingHypId(null);
      setVoteComment("");
      qc.invalidateQueries({ queryKey: ["hypotheses"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const toggleSelect = (id: string) => {
    const next = new Set(selectedIds);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelectedIds(next);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div
        className="flex items-center justify-between px-5 py-3 border-b"
        style={{ borderColor: "var(--border)", background: "var(--surface)" }}
      >
        <div>
          <h1 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Подготовка к комитету
          </h1>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
            {readyHyps.length} гипотез готово к рассмотрению
          </p>
        </div>
        <div className="flex items-center gap-2">
          {selectedIds.size > 0 && (
            <button
              onClick={() => reportMutation.mutate()}
              disabled={reportMutation.isPending}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm"
              style={{ background: "var(--accent)", color: "white" }}
            >
              <FileText size={13} />
              {reportMutation.isPending ? "Генерирую..." : `Отчёт (${selectedIds.size})`}
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Hypothesis list */}
        <div className="flex-1 overflow-auto p-4">
          {readyHyps.length === 0 ? (
            <div className="text-sm mt-8 text-center" style={{ color: "var(--text-muted)" }}>
              Нет гипотез со статусом «Готов к комитету»
            </div>
          ) : (
            <div className="space-y-2">
              {readyHyps.map((h) => (
                <div
                  key={h.id}
                  className="flex items-start gap-3 p-3 rounded border"
                  style={{
                    borderColor: selectedIds.has(h.id) ? "var(--accent)" : "var(--border)",
                    background: "var(--surface)",
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedIds.has(h.id)}
                    onChange={() => toggleSelect(h.id)}
                    className="mt-1 accent-purple-600"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                        {h.title}
                      </p>
                      {h.overall_score != null && (
                        <span className="text-xs px-1.5 py-0.5 rounded"
                          style={{ background: "var(--raised)", color: "var(--accent)" }}>
                          {h.overall_score.toFixed(1)}/10
                        </span>
                      )}
                    </div>
                    <p className="text-xs mt-0.5 line-clamp-2" style={{ color: "var(--text-secondary)" }}>
                      {h.short_description}
                    </p>
                    <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                      Обновлено: {formatDate(h.updated_at)}
                      {h.confidence_score > 0 && ` · Уверенность: ${Math.round(h.confidence_score * 100)}%`}
                    </p>
                  </div>

                  {/* Vote button */}
                  <div className="flex-shrink-0">
                    {votingHypId === h.id ? (
                      <div className="space-y-1.5" style={{ minWidth: 200 }}>
                        <textarea
                          value={voteComment}
                          onChange={(e) => setVoteComment(e.target.value)}
                          placeholder="Комментарий (обязателен)"
                          rows={2}
                          className="w-full px-2 py-1.5 text-xs rounded border"
                          style={{
                            background: "var(--raised)", borderColor: "var(--border)",
                            color: "var(--text-primary)",
                          }}
                        />
                        <div className="grid grid-cols-2 gap-1">
                          {VOTES.map((v) => (
                            <button
                              key={v.value}
                              disabled={!voteComment.trim() || voteMutation.isPending}
                              onClick={() => voteMutation.mutate({ hypothesisId: h.id, vote: v.value })}
                              className="text-xs px-2 py-1.5 rounded border transition-colors"
                              style={{ borderColor: "var(--border)", color: v.color }}
                            >
                              {v.label}
                            </button>
                          ))}
                        </div>
                        <button
                          onClick={() => setVotingHypId(null)}
                          className="text-xs w-full"
                          style={{ color: "var(--text-muted)" }}
                        >
                          Отмена
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setVotingHypId(h.id)}
                        className="text-xs px-2.5 py-1.5 rounded border"
                        style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
                      >
                        Голосовать
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Report panel */}
        {generatedReport && (
          <div
            className="w-96 flex-shrink-0 border-l overflow-auto p-4"
            style={{ borderColor: "var(--border)" }}
          >
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-xs font-semibold" style={{ color: "var(--text-muted)" }}>
                Executive Summary
              </h2>
              <button
                onClick={() => setGeneratedReport(null)}
                className="text-xs"
                style={{ color: "var(--text-muted)" }}
              >
                Закрыть
              </button>
            </div>
            <pre
              className="text-xs whitespace-pre-wrap leading-relaxed"
              style={{ color: "var(--text-secondary)", fontFamily: "inherit" }}
            >
              {generatedReport}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
