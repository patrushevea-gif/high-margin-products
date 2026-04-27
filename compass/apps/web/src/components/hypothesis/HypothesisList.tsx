"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { Hypothesis } from "@/types";
import { STATUS_LABELS, STATUS_COLORS, DOMAIN_LABELS, formatDate, cn } from "@/lib/utils";
import { Plus, Filter } from "lucide-react";

export function HypothesisList() {
  const params = useSearchParams();
  const status = params.get("status") ?? undefined;
  const domain = params.get("domain") ?? undefined;

  const qs = new URLSearchParams();
  if (status) qs.set("status", status);
  if (domain) qs.set("domain", domain);

  const { data: hypotheses = [], isLoading } = useQuery<Hypothesis[]>({
    queryKey: ["hypotheses", status, domain],
    queryFn: () => api.get<Hypothesis[]>(`/hypotheses?${qs}&limit=200`),
  });

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div
        className="flex items-center justify-between px-5 py-3 border-b"
        style={{ borderColor: "var(--border)", background: "var(--surface)" }}
      >
        <div>
          <h1 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Гипотезы
          </h1>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
            {hypotheses.length} записей
          </p>
        </div>
        <Link
          href="/hypotheses/new"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm"
          style={{ background: "var(--accent)", color: "white" }}
        >
          <Plus size={14} /> Создать
        </Link>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <div className="p-5 space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-10 rounded animate-pulse" style={{ background: "var(--surface)" }} />
            ))}
          </div>
        ) : (
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr style={{ background: "var(--surface)", borderBottom: "1px solid var(--border)" }}>
                {["Гипотеза", "Домен", "Статус", "Уверенность", "Оценка", "Обновлено"].map((col) => (
                  <th
                    key={col}
                    className="text-left px-4 py-2.5 font-medium text-xs"
                    style={{ color: "var(--text-muted)" }}
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {hypotheses.map((h) => (
                <tr
                  key={h.id}
                  className="border-b hover:bg-background-surface transition-colors"
                  style={{ borderColor: "var(--border)" }}
                >
                  <td className="px-4 py-2.5">
                    <Link
                      href={`/hypotheses/${h.id}`}
                      className="font-medium hover:underline"
                      style={{ color: "var(--text-primary)" }}
                    >
                      {h.title}
                    </Link>
                    {h.war_room_active && (
                      <span className="ml-2 text-xs" style={{ color: "var(--danger)" }}>WAR ROOM</span>
                    )}
                    <p className="text-xs mt-0.5 line-clamp-1" style={{ color: "var(--text-muted)" }}>
                      {h.short_description}
                    </p>
                  </td>
                  <td className="px-4 py-2.5 text-xs" style={{ color: "var(--text-muted)" }}>
                    {DOMAIN_LABELS[h.domain] ?? h.domain}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={cn("text-xs", STATUS_COLORS[h.status])}>
                      {STATUS_LABELS[h.status] ?? h.status}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-xs" style={{ color: "var(--text-secondary)" }}>
                    {h.confidence_score > 0 ? `${Math.round(h.confidence_score * 100)}%` : "—"}
                  </td>
                  <td className="px-4 py-2.5 text-xs" style={{ color: "var(--text-secondary)" }}>
                    {h.overall_score != null ? h.overall_score.toFixed(1) : "—"}
                  </td>
                  <td className="px-4 py-2.5 text-xs" style={{ color: "var(--text-muted)" }}>
                    {formatDate(h.updated_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
