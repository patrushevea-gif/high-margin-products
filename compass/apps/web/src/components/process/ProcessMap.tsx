"use client";

import { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ReactFlow, Background, Controls, MarkerType, Handle, Position,
  type Node, type Edge, type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { api } from "@/lib/api";
import { Activity, Map } from "lucide-react";

interface AgentRun {
  id: string;
  agent_name: string;
  status: string;
  started_at: string;
  finished_at?: string;
  cost_usd?: number;
}

const AGENTS = [
  { id: "scout", label: "Scout", desc: "Разведчик", x: 50, y: 200 },
  { id: "curator", label: "Curator", desc: "Куратор", x: 250, y: 200 },
  { id: "tech_analyst", label: "TechAnalyst", desc: "Технолог", x: 450, y: 80 },
  { id: "market_analyst", label: "MarketAnalyst", desc: "Маркетолог", x: 450, y: 200 },
  { id: "economist", label: "Economist", desc: "Финансист", x: 450, y: 320 },
  { id: "compliance_officer", label: "Compliance", desc: "Комплаенс", x: 450, y: 440 },
  { id: "synthesizer", label: "Synthesizer", desc: "Синтезатор", x: 680, y: 250 },
  { id: "devils_advocate", label: "DevilsAdvocate", desc: "Адв. дьявола", x: 880, y: 200 },
  { id: "committee", label: "Committee", desc: "Комитет", x: 1080, y: 200 },
];

const EDGE_DEFS: Edge[] = [
  { id: "e1", source: "scout", target: "curator" },
  { id: "e2", source: "curator", target: "tech_analyst" },
  { id: "e3", source: "curator", target: "market_analyst" },
  { id: "e4", source: "curator", target: "economist" },
  { id: "e5", source: "curator", target: "compliance_officer" },
  { id: "e6", source: "tech_analyst", target: "synthesizer" },
  { id: "e7", source: "market_analyst", target: "synthesizer" },
  { id: "e8", source: "economist", target: "synthesizer" },
  { id: "e9", source: "compliance_officer", target: "synthesizer" },
  { id: "e10", source: "synthesizer", target: "devils_advocate" },
  { id: "e11", source: "devils_advocate", target: "committee" },
];

const STATUS_STYLE: Record<string, { border: string; bg: string; dot: string }> = {
  running:   { border: "#7c3aed", bg: "rgba(124,58,237,0.15)", dot: "#7c3aed" },
  success:   { border: "#10b981", bg: "rgba(16,185,129,0.10)", dot: "#10b981" },
  failed:    { border: "#ef4444", bg: "rgba(239,68,68,0.10)",  dot: "#ef4444" },
  idle:      { border: "var(--border)", bg: "var(--surface)", dot: "transparent" },
};

function AgentNode({ data }: NodeProps) {
  const s = STATUS_STYLE[(data.status as string) ?? "idle"];
  return (
    <div className="px-3 py-2 rounded border text-xs"
      style={{ background: s.bg, borderColor: s.border, color: "var(--text-primary)", minWidth: 118 }}>
      <Handle type="target" position={Position.Left} style={{ background: s.border }} />
      <div className="flex items-center gap-1.5">
        {s.dot !== "transparent" && (
          <span className="w-1.5 h-1.5 rounded-full flex-shrink-0"
            style={{ background: s.dot, animation: data.status === "running" ? "pulse 1s infinite" : "none" }} />
        )}
        <span className="font-semibold">{data.label as string}</span>
      </div>
      <div style={{ color: "var(--text-muted)" }}>{data.desc as string}</div>
      {data.runs != null && (
        <div className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
          {data.runs} запусков
        </div>
      )}
      <Handle type="source" position={Position.Right} style={{ background: s.border }} />
    </div>
  );
}

const nodeTypes = { agentNode: AgentNode };

export function ProcessMap() {
  const [liveMode, setLiveMode] = useState(false);

  const { data: runs = [] } = useQuery<AgentRun[]>({
    queryKey: ["agent-runs-live"],
    queryFn: () => api.get<AgentRun[]>("/agents/runs?limit=50"),
    refetchInterval: liveMode ? 4000 : false,
    enabled: liveMode,
  });

  const runsByAgent = runs.reduce<Record<string, AgentRun[]>>((acc, r) => {
    (acc[r.agent_name] ??= []).push(r);
    return acc;
  }, {});

  const nodes: Node[] = AGENTS.map((a) => {
    const agentRuns = runsByAgent[a.id] ?? [];
    const latest = agentRuns[0];
    const status = liveMode
      ? latest?.status === "running" ? "running"
        : latest?.status === "success" ? "success"
        : latest?.status === "failed" ? "failed"
        : "idle"
      : "idle";
    return {
      id: a.id,
      type: "agentNode",
      position: { x: a.x, y: a.y },
      data: { label: a.label, desc: a.desc, status, runs: liveMode ? agentRuns.length : null },
    };
  });

  const edges: Edge[] = EDGE_DEFS.map((e) => ({
    ...e,
    animated: liveMode,
    style: { stroke: "var(--border)" },
    markerEnd: { type: MarkerType.ArrowClosed, color: "var(--border)" },
  }));

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-5 py-3 border-b"
        style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
        <div>
          <h1 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Карта процесса</h1>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
            {liveMode ? "Живой режим — обновление каждые 4 сек" : "Статическая схема пайплайна"}
          </p>
        </div>
        <button
          onClick={() => setLiveMode((v) => !v)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors"
          style={{
            background: liveMode ? "rgba(124,58,237,0.15)" : "var(--raised)",
            color: liveMode ? "var(--accent)" : "var(--text-secondary)",
            border: `1px solid ${liveMode ? "var(--accent)" : "var(--border)"}`,
          }}
        >
          {liveMode ? <Activity size={12} /> : <Map size={12} />}
          {liveMode ? "Live" : "Статика"}
        </button>
      </div>
      <div className="flex-1" style={{ background: "var(--background)" }}>
        <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView
          style={{ background: "var(--background)" }}>
          <Background color="var(--border)" gap={20} />
          <Controls style={{ background: "var(--surface)", border: "1px solid var(--border)" }} />
        </ReactFlow>
      </div>
    </div>
  );
}
