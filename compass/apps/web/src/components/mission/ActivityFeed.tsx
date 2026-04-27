"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

interface AgentRun {
  id: string;
  agent_name: string;
  status: string;
  started_at: string;
  cost_usd: number;
}

export function ActivityFeed() {
  const { data: runs = [] } = useQuery<AgentRun[]>({
    queryKey: ["agent-runs"],
    queryFn: () => api.get<AgentRun[]>("/agents/runs?limit=30"),
    refetchInterval: 10_000,
  });

  const AGENT_ICONS: Record<string, string> = {
    scout: "S",
    curator: "C",
    tech_analyst: "T",
    market_analyst: "M",
    economist: "E",
    compliance_officer: "Co",
    synthesizer: "Sy",
    devils_advocate: "D",
    orchestrator: "O",
  };

  return (
    <div className="flex flex-col h-full">
      <div
        className="px-3 py-2.5 text-xs font-medium border-b"
        style={{ color: "var(--text-muted)", borderColor: "var(--border)" }}
      >
        Активность
      </div>
      <div className="flex-1 overflow-auto">
        {runs.length === 0 ? (
          <div className="px-3 py-4 text-xs" style={{ color: "var(--text-muted)" }}>
            Нет активности
          </div>
        ) : (
          runs.map((run) => (
            <div
              key={run.id}
              className="px-3 py-2 border-b text-xs"
              style={{ borderColor: "var(--border)" }}
            >
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
                <span
                  className="ml-auto"
                  style={{
                    color: run.status === "completed"
                      ? "var(--success)"
                      : run.status === "failed"
                      ? "var(--danger)"
                      : "var(--warning)",
                  }}
                >
                  {run.status === "running" ? "..." : run.status === "completed" ? "ok" : "err"}
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
