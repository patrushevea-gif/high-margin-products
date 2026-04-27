"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Hypothesis } from "@/types";
import { STATUS_LABELS, STATUS_COLORS, formatDate } from "@/lib/utils";
import { HypothesisFunnel } from "./HypothesisFunnel";
import { ActivityFeed } from "./ActivityFeed";
import { AttentionList } from "./AttentionList";
import { StatsBar } from "./StatsBar";

const PIPELINE_STAGES = [
  "draft", "signal_processed", "tech_evaluated",
  "market_evaluated", "economics_evaluated", "compliance_checked",
  "synthesized", "challenged", "committee_ready",
];

export function MissionControl() {
  const { data: hypotheses = [], isLoading } = useQuery<Hypothesis[]>({
    queryKey: ["hypotheses"],
    queryFn: () => api.get<Hypothesis[]>("/hypotheses?limit=200"),
  });

  const byStatus = PIPELINE_STAGES.reduce<Record<string, Hypothesis[]>>((acc, s) => {
    acc[s] = hypotheses.filter((h) => h.status === s);
    return acc;
  }, {});

  const warRoomActive = hypotheses.filter((h) => h.war_room_active);
  const needsAttention = hypotheses.filter(
    (h) => h.status === "to_review" || h.war_room_active
  );

  return (
    <div className="flex flex-col h-full">
      {/* Top bar */}
      <div
        className="flex items-center justify-between px-5 py-3 border-b text-sm"
        style={{ borderColor: "var(--border)", background: "var(--surface)" }}
      >
        <div className="flex items-center gap-4">
          <span style={{ color: "var(--text-muted)" }}>Mission Control</span>
          {warRoomActive.length > 0 && (
            <span className="px-2 py-0.5 rounded text-xs font-medium animate-pulse"
              style={{ background: "rgba(239,68,68,0.15)", color: "var(--danger)" }}>
              WAR ROOM ACTIVE ({warRoomActive.length})
            </span>
          )}
        </div>
        <div className="flex items-center gap-4">
          <span style={{ color: "var(--text-muted)" }}>
            {hypotheses.length} гипотез всего
          </span>
        </div>
      </div>

      {/* Main 3-column layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Activity feed */}
        <div
          className="w-56 flex-shrink-0 border-r overflow-auto"
          style={{ borderColor: "var(--border)" }}
        >
          <ActivityFeed />
        </div>

        {/* Center: Funnel */}
        <div className="flex-1 overflow-auto px-5 py-4">
          <StatsBar hypotheses={hypotheses} />
          <HypothesisFunnel byStatus={byStatus} stages={PIPELINE_STAGES} isLoading={isLoading} />
        </div>

        {/* Right: Attention */}
        <div
          className="w-64 flex-shrink-0 border-l overflow-auto"
          style={{ borderColor: "var(--border)" }}
        >
          <AttentionList items={needsAttention} />
        </div>
      </div>
    </div>
  );
}
