"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { useRealtimeTable } from "@/hooks/useRealtimeTable";
import { isRealtimeAvailable } from "@/lib/supabase";
import { Wifi, WifiOff } from "lucide-react";

interface AgentRun {
  id: string;
  agent_name: string;
  status: string;
  started_at: string;
  cost_usd: number;
}

const AGENT_ICONS: Record<string, string> = {
  scout: "S", curator: "C", tech_analyst: "T", market_analyst: "M",
  economist: "E", compliance_officer: "Co", synthesizer: "Sy",
  devils_advocate: "D", orchestrator: "O",
};

const STATUS_COLOR: Record<string, string> = {
  running: "var(--warning)",
  success: "var(--success)",
  completed: "var(--success)",
  failed: "var(--danger)",
};

export function ActivityFeed() {
  // Realtime: push updates via Supabase WebSocket
  useRealtimeTable("agent_runs", {
    invalidateKeys: [["agent-runs"]],
    event: "INSERT",
  });

  // Fallback polling when Supabase not configured (10s)
  const { data: runs = [] } = useQuery<AgentRun[]>({
    queryKey: ["agent-runs"],
    queryFn: () => api.get<AgentRun[]>("/agents/runs?limit=30"),
    refetchInterval: isRealtimeAvailable ? false : 10_000,
  });

  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-2.5 text-xs font-medium border-b flex items-center justify-between"
        style={{ color: "var(--text-muted)", borderColor: "var(--border)" }}>
        <span>Активность</span>
        <span title={isRealtimeAvailable ? "Realtime WebSocket" : "Polling каждые 10 сек"}>
          {isRealtimeAvailable
            ? <Wifi size={11} style={{ color: "var(--success)" }} />
            : <WifiOff size={11} style={{ color: "var(--text-muted)" }} />}
        </span>
      </div>

      <div className="flex-1 overflow-auto">
        {runs.length === 0 ? (
          <div className="px-3 py-4 text-xs" style={{ color: "var(--text-muted)" }}>
            Нет активности
          </div>
        ) : (
          runs.map((run) => (
            <div key={run.id} className="px-3 py-2 border-b text-xs"
              style={{ borderColor: "var(--border)" }}>
              <div className="flex items-center gap-1.5 mb-0.5">
                <span
                  className="w-4 h-4 rounded-sm flex items-center justify-center text-[10px] font-bold flex-shrink-0"
                  style={{ background: "var(--accent)", color: "white" }}
                >
                  {AGENT_ICONS[run.agent_name] ?? "?"}
                </span>
                <span className="font-medium" style={{ color: "var(--text-primary)" }}>
                  {run.agent_name}
                </span>
                <span className="ml-auto" style={{ color: STATUS_COLOR[run.status] ?? "var(--text-muted)" }}>
                  {run.status === "running" ? "···" : run.status === "success" || run.status === "completed" ? "ok" : "err"}
                </span>
              </div>
              <div style={{ color: "var(--text-muted)" }}>
                {formatDate(run.started_at)}
                {run.cost_usd > 0 && ` · $${run.cost_usd.toFixed(4)}`}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
