"use client";

import Link from "next/link";
import { Hypothesis } from "@/types";
import { AlertTriangle, Zap } from "lucide-react";

interface Props {
  items: Hypothesis[];
}

export function AttentionList({ items }: Props) {
  return (
    <div className="flex flex-col h-full">
      <div
        className="px-3 py-2.5 text-xs font-medium border-b"
        style={{ color: "var(--text-muted)", borderColor: "var(--border)" }}
      >
        Требуют внимания
      </div>
      <div className="flex-1 overflow-auto">
        {items.length === 0 ? (
          <div className="px-3 py-4 text-xs" style={{ color: "var(--text-muted)" }}>
            Нет элементов
          </div>
        ) : (
          items.map((h) => (
            <Link
              key={h.id}
              href={`/hypotheses/${h.id}`}
              className="block px-3 py-2.5 border-b hover:bg-background-raised transition-colors"
              style={{ borderColor: "var(--border)" }}
            >
              <div className="flex items-start gap-2">
                {h.war_room_active ? (
                  <Zap size={12} className="mt-0.5 flex-shrink-0" style={{ color: "var(--danger)" }} />
                ) : (
                  <AlertTriangle size={12} className="mt-0.5 flex-shrink-0" style={{ color: "var(--warning)" }} />
                )}
                <div>
                  <div className="text-xs font-medium leading-snug" style={{ color: "var(--text-primary)" }}>
                    {h.title}
                  </div>
                  <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                    {h.war_room_active ? "War Room активен" : "Требует пересмотра"}
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
