"use client";

import Link from "next/link";
import { Hypothesis } from "@/types";
import { STATUS_LABELS, STATUS_COLORS, cn } from "@/lib/utils";
import { ChevronRight } from "lucide-react";

interface Props {
  byStatus: Record<string, Hypothesis[]>;
  stages: string[];
  isLoading: boolean;
}

export function HypothesisFunnel({ byStatus, stages, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="space-y-2 mt-4">
        {stages.map((s) => (
          <div key={s} className="h-16 rounded animate-pulse" style={{ background: "var(--surface)" }} />
        ))}
      </div>
    );
  }

  return (
    <div className="mt-4 space-y-2">
      {stages.map((stage) => {
        const items = byStatus[stage] ?? [];
        return (
          <div
            key={stage}
            className="rounded border overflow-hidden"
            style={{ borderColor: "var(--border)", background: "var(--surface)" }}
          >
            {/* Stage header */}
            <div
              className="flex items-center justify-between px-3 py-2"
              style={{ borderBottom: items.length > 0 ? `1px solid var(--border)` : "none" }}
            >
              <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                {STATUS_LABELS[stage] ?? stage}
              </span>
              <span
                className="text-xs px-1.5 py-0.5 rounded-full"
                style={{ background: "var(--raised)", color: "var(--text-muted)" }}
              >
                {items.length}
              </span>
            </div>

            {/* Top 3 items */}
            {items.slice(0, 3).map((h) => (
              <Link
                key={h.id}
                href={`/hypotheses/${h.id}`}
                className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-background-raised transition-colors border-b last:border-b-0"
                style={{ borderColor: "var(--border)" }}
              >
                <span className="flex-1 truncate" style={{ color: "var(--text-primary)" }}>
                  {h.title}
                </span>
                {h.confidence_score > 0 && (
                  <span className="text-xs flex-shrink-0" style={{ color: "var(--text-muted)" }}>
                    {Math.round(h.confidence_score * 100)}%
                  </span>
                )}
                <ChevronRight size={12} style={{ color: "var(--text-muted)" }} />
              </Link>
            ))}

            {items.length > 3 && (
              <Link
                href={`/hypotheses?status=${stage}`}
                className="flex items-center px-3 py-1.5 text-xs"
                style={{ color: "var(--accent)" }}
              >
                +{items.length - 3} ещё
              </Link>
            )}
          </div>
        );
      })}
    </div>
  );
}
