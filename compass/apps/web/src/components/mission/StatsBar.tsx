"use client";

import { Hypothesis } from "@/types";

interface Props {
  hypotheses: Hypothesis[];
}

export function StatsBar({ hypotheses }: Props) {
  const total = hypotheses.length;
  const accepted = hypotheses.filter((h) => h.status === "accepted").length;
  const rejected = hypotheses.filter((h) => h.status === "rejected").length;
  const inProgress = hypotheses.filter(
    (h) => !["accepted", "rejected", "parked", "draft"].includes(h.status)
  ).length;
  const committeReady = hypotheses.filter((h) => h.status === "committee_ready").length;
  const warRoom = hypotheses.filter((h) => h.war_room_active).length;

  const stats = [
    { label: "Всего", value: total, color: "var(--text-primary)" },
    { label: "В работе", value: inProgress, color: "var(--info)" },
    { label: "К комитету", value: committeReady, color: "var(--accent)" },
    { label: "Принято", value: accepted, color: "var(--success)" },
    { label: "War Room", value: warRoom, color: warRoom > 0 ? "#ef4444" : "var(--text-muted)" },
  ];

  return (
    <div
      className="flex gap-4 p-3 rounded border mb-4"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      {stats.map(({ label, value, color }) => (
        <div key={label} className="flex-1 text-center">
          <div className="text-lg font-semibold leading-none" style={{ color }}>
            {value}
          </div>
          <div className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
            {label}
          </div>
        </div>
      ))}
    </div>
  );
}
