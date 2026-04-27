"use client";

import Link from "next/link";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Hypothesis } from "@/types";
import { AlertTriangle, Zap, ZapOff } from "lucide-react";
import { toast } from "sonner";

interface Props {
  items: Hypothesis[];
}

export function AttentionList({ items }: Props) {
  const warRoom = items.filter((h) => h.war_room_active);
  const toReview = items.filter((h) => !h.war_room_active);

  return (
    <div className="flex flex-col h-full">
      {warRoom.length > 0 && (
        <div>
          <div className="px-3 py-2 text-xs font-medium border-b flex items-center gap-1.5"
            style={{ color: "#ef4444", borderColor: "var(--border)", background: "rgba(239,68,68,0.06)" }}>
            <Zap size={11} />
            War Room ({warRoom.length})
          </div>
          {warRoom.map((h) => (
            <WarRoomItem key={h.id} h={h} />
          ))}
        </div>
      )}

      <div className="px-3 py-2 text-xs font-medium border-b"
        style={{ color: "var(--text-muted)", borderColor: "var(--border)" }}>
        Требуют пересмотра{toReview.length > 0 ? ` (${toReview.length})` : ""}
      </div>
      <div className="flex-1 overflow-auto">
        {toReview.length === 0 ? (
          <div className="px-3 py-4 text-xs" style={{ color: "var(--text-muted)" }}>
            Нет элементов
          </div>
        ) : (
          toReview.map((h) => (
            <Link key={h.id} href={`/hypotheses/${h.id}`}
              className="block px-3 py-2.5 border-b hover:bg-white/5 transition-colors"
              style={{ borderColor: "var(--border)" }}>
              <div className="flex items-start gap-2">
                <AlertTriangle size={12} className="mt-0.5 flex-shrink-0" style={{ color: "#f59e0b" }} />
                <div>
                  <div className="text-xs font-medium leading-snug" style={{ color: "var(--text-primary)" }}>
                    {h.title}
                  </div>
                  <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                    Требует пересмотра
                  </div>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}

function WarRoomItem({ h }: { h: Hypothesis }) {
  const qc = useQueryClient();
  const deactivate = useMutation({
    mutationFn: () => api.patch(`/hypotheses/${h.id}`, { war_room_active: false }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["hypotheses"] });
      toast.success("War Room деактивирован");
    },
  });

  return (
    <div className="flex items-start gap-2 px-3 py-2.5 border-b"
      style={{ borderColor: "var(--border)", background: "rgba(239,68,68,0.04)" }}>
      <div className="w-1 self-stretch rounded" style={{ background: "#ef4444", flexShrink: 0 }} />
      <div className="flex-1 min-w-0">
        <Link href={`/hypotheses/${h.id}`}
          className="text-xs font-medium leading-snug hover:underline line-clamp-2"
          style={{ color: "var(--text-primary)" }}>
          {h.title}
        </Link>
        {h.overall_score != null && (
          <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
            Оценка: {h.overall_score.toFixed(1)}/10
          </p>
        )}
      </div>
      <button
        onClick={() => deactivate.mutate()}
        title="Деактивировать War Room"
        className="flex-shrink-0 p-1 rounded hover:bg-white/10 transition-colors"
      >
        <ZapOff size={11} style={{ color: "#ef4444" }} />
      </button>
    </div>
  );
}
