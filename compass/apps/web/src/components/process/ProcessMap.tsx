"use client";

import { useCallback } from "react";
import {
  ReactFlow, Background, Controls, Handle, Position,
  type Node, type Edge, type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

const AGENTS = [
  { id: "scout", label: "Scout", desc: "Разведчик", x: 50, y: 200 },
  { id: "curator", label: "Curator", desc: "Куратор", x: 250, y: 200 },
  { id: "tech_analyst", label: "TechAnalyst", desc: "Технолог", x: 450, y: 100 },
  { id: "market_analyst", label: "MarketAnalyst", desc: "Маркетолог", x: 450, y: 200 },
  { id: "economist", label: "Economist", desc: "Финансист", x: 450, y: 300 },
  { id: "compliance", label: "Compliance", desc: "Комплаенс", x: 450, y: 400 },
  { id: "synthesizer", label: "Synthesizer", desc: "Методист", x: 650, y: 250 },
  { id: "devils", label: "DevilsAdvocate", desc: "Адв. дьявола", x: 850, y: 200 },
  { id: "committee", label: "Committee", desc: "Комитет", x: 1050, y: 200 },
];

const EDGES: Edge[] = [
  { id: "e1", source: "scout", target: "curator", animated: true },
  { id: "e2", source: "curator", target: "tech_analyst", animated: true },
  { id: "e3", source: "curator", target: "market_analyst", animated: true },
  { id: "e4", source: "curator", target: "economist", animated: true },
  { id: "e5", source: "curator", target: "compliance", animated: true },
  { id: "e6", source: "tech_analyst", target: "synthesizer", animated: true },
  { id: "e7", source: "market_analyst", target: "synthesizer", animated: true },
  { id: "e8", source: "economist", target: "synthesizer", animated: true },
  { id: "e9", source: "compliance", target: "synthesizer", animated: true },
  { id: "e10", source: "synthesizer", target: "devils", animated: true },
  { id: "e11", source: "devils", target: "committee", animated: false },
];

function AgentNode({ data }: NodeProps) {
  return (
    <div
      className="px-3 py-2 rounded border text-xs"
      style={{
        background: "var(--surface)",
        borderColor: "var(--accent)",
        color: "var(--text-primary)",
        minWidth: 110,
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: "var(--accent)" }} />
      <div className="font-semibold">{data.label as string}</div>
      <div style={{ color: "var(--text-muted)" }}>{data.desc as string}</div>
      <Handle type="source" position={Position.Right} style={{ background: "var(--accent)" }} />
    </div>
  );
}

const nodeTypes = { agentNode: AgentNode };

const initialNodes: Node[] = AGENTS.map((a) => ({
  id: a.id,
  type: "agentNode",
  position: { x: a.x, y: a.y },
  data: { label: a.label, desc: a.desc },
}));

const initialEdges: Edge[] = EDGES.map((e) => ({
  ...e,
  style: { stroke: "var(--border)" },
  markerEnd: { type: "ArrowClosed" as const, color: "var(--border)" },
}));

export function ProcessMap() {
  return (
    <div className="flex flex-col h-full">
      <div
        className="px-5 py-3 border-b"
        style={{ borderColor: "var(--border)", background: "var(--surface)" }}
      >
        <h1 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          Карта процесса
        </h1>
        <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
          Живая документация агентного пайплайна
        </p>
      </div>
      <div className="flex-1" style={{ background: "var(--background)" }}>
        <ReactFlow
          nodes={initialNodes}
          edges={initialEdges}
          nodeTypes={nodeTypes}
          fitView
          style={{ background: "var(--background)" }}
        >
          <Background color="var(--border)" gap={20} />
          <Controls style={{ background: "var(--surface)", border: "1px solid var(--border)" }} />
        </ReactFlow>
      </div>
    </div>
  );
}
