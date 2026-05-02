"use client";

import { useQuery } from "@tanstack/react-query";
import { useCallback, useState } from "react";
import { api } from "@/lib/api";
import {
  ReactFlow, Background, Controls, MiniMap, MarkerType,
  Handle, Position, type Node, type Edge, type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { cn } from "@/lib/utils";

interface GraphData {
  nodes: Array<{
    id: string;
    label: string;
    type: "hypothesis" | "signal";
    status?: string;
    score?: number;
    domain?: string;
    source_type?: string;
    relevance?: number;
  }>;
  edges: Array<{ id: string; source: string; target: string; type: string }>;
}

const NODE_COLORS = {
  hypothesis: { accepted: "#10B981", rejected: "#EF4444", committee_ready: "#7C3AED", default: "#3B82F6" },
  signal: { patents: "#F59E0B", scientific: "#8B5CF6", news: "#06B6D4", competitors: "#EF4444", default: "#6B7280" },
};

function HypothesisNode({ data }: NodeProps) {
  const color = NODE_COLORS.hypothesis[(data.status as keyof typeof NODE_COLORS.hypothesis)] ?? NODE_COLORS.hypothesis.default;
  return (
    <div className="relative" style={{ minWidth: 140 }}>
      <Handle type="target" position={Position.Left} style={{ background: color }} />
      <div className="px-2.5 py-2 rounded border text-xs"
        style={{ background: "var(--surface)", borderColor: color, borderWidth: 1.5 }}>
        <div className="font-medium mb-0.5 line-clamp-2" style={{ color: "var(--text-primary)", fontSize: 11 }}>
          {data.label as string}
        </div>
        {data.score != null && (
          <div style={{ color }}>{(data.score as number).toFixed(1)}/10</div>
        )}
      </div>
      <Handle type="source" position={Position.Right} style={{ background: color }} />
    </div>
  );
}

function SignalNode({ data }: NodeProps) {
  const color = NODE_COLORS.signal[(data.source_type as keyof typeof NODE_COLORS.signal)] ?? NODE_COLORS.signal.default;
  return (
    <div className="relative">
      <div className="px-2 py-1.5 rounded text-xs"
        style={{ background: "var(--raised)", border: `1px dashed ${color}`, maxWidth: 120 }}>
        <div className="line-clamp-2" style={{ color: "var(--text-secondary)", fontSize: 10 }}>
          {data.label as string}
        </div>
      </div>
      <Handle type="source" position={Position.Right} style={{ background: color }} />
    </div>
  );
}

const nodeTypes = { hypothesis: HypothesisNode, signal: SignalNode };

function buildLayout(rawNodes: GraphData["nodes"]): Node[] {
  // Simple grid layout — hypotheses left, signals right
  const hyps = rawNodes.filter((n) => n.type === "hypothesis");
  const sigs = rawNodes.filter((n) => n.type === "signal");

  const nodes: Node[] = [];
  hyps.forEach((n, i) => {
    nodes.push({
      id: n.id,
      type: "hypothesis",
      position: { x: 300, y: i * 80 },
      data: n,
    });
  });
  sigs.forEach((n, i) => {
    nodes.push({
      id: n.id,
      type: "signal",
      position: { x: 0, y: i * 50 },
      data: n,
    });
  });
  return nodes;
}

export function KnowledgeGraph() {
  const [filter, setFilter] = useState<"all" | "hypothesis" | "signal">("all");
  const [selectedNode, setSelectedNode] = useState<any>(null);

  const { data, isLoading } = useQuery<GraphData>({
    queryKey: ["graph"],
    queryFn: () => api.get<GraphData>("/graph/nodes"),
  });

  const filteredNodes = (data?.nodes ?? []).filter(
    (n) => filter === "all" || n.type === filter
  );
  const nodeIds = new Set(filteredNodes.map((n) => n.id));
  const filteredEdges = (data?.edges ?? []).filter(
    (e) => nodeIds.has(e.source) && nodeIds.has(e.target)
  );

  const flowNodes = buildLayout(filteredNodes);
  const flowEdges: Edge[] = filteredEdges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    style: { stroke: "var(--border)" },
    markerEnd: { type: MarkerType.ArrowClosed, color: "var(--border)" },
  }));

  const onNodeClick = useCallback((_: any, node: Node) => {
    setSelectedNode(node.data);
  }, []);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b"
        style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
        <div>
          <h1 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Knowledge Graph
          </h1>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
            {filteredNodes.length} узлов · {filteredEdges.length} связей
          </p>
        </div>
        <div className="flex gap-1">
          {(["all", "hypothesis", "signal"] as const).map((f) => (
            <button key={f} onClick={() => setFilter(f)}
              className="text-xs px-2.5 py-1 rounded border transition-colors"
              style={{
                borderColor: filter === f ? "var(--accent)" : "var(--border)",
                color: filter === f ? "var(--accent)" : "var(--text-muted)",
                background: filter === f ? "rgba(124,58,237,0.08)" : "transparent",
              }}>
              {f === "all" ? "Все" : f === "hypothesis" ? "Гипотезы" : "Сигналы"}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Graph */}
        <div className="flex-1" style={{ background: "var(--background)" }}>
          {isLoading ? (
            <div className="flex items-center justify-center h-full text-sm" style={{ color: "var(--text-muted)" }}>
              Загрузка графа...
            </div>
          ) : (
            <ReactFlow
              nodes={flowNodes}
              edges={flowEdges}
              nodeTypes={nodeTypes}
              onNodeClick={onNodeClick}
              fitView
              style={{ background: "var(--background)" }}
            >
              <Background color="var(--border)" gap={30} />
              <Controls style={{ background: "var(--surface)", border: "1px solid var(--border)" }} />
              <MiniMap
                style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
                nodeColor={(n) => {
                  const d = n.data as any;
                  return NODE_COLORS.hypothesis[d.status as keyof typeof NODE_COLORS.hypothesis] ?? "#3B82F6";
                }}
              />
            </ReactFlow>
          )}
        </div>

        {/* Side panel */}
        {selectedNode && (
          <div className="w-56 flex-shrink-0 border-l p-3 overflow-auto"
            style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>Узел</span>
              <button onClick={() => setSelectedNode(null)}
                className="text-xs" style={{ color: "var(--text-muted)" }}>✕</button>
            </div>
            <p className="text-xs font-medium mb-1" style={{ color: "var(--text-primary)" }}>
              {selectedNode.label}
            </p>
            <p className="text-xs mb-2" style={{ color: "var(--text-muted)" }}>
              {selectedNode.type === "hypothesis" ? "Гипотеза" : "Сигнал"}
            </p>
            {selectedNode.status && (
              <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                Статус: {selectedNode.status}
              </p>
            )}
            {selectedNode.score != null && (
              <p className="text-xs" style={{ color: "var(--accent)" }}>
                Оценка: {selectedNode.score.toFixed(1)}/10
              </p>
            )}
            {selectedNode.type === "hypothesis" && (
              <a href={`/hypotheses/${selectedNode.id}`}
                className="block mt-3 text-xs text-center px-2 py-1.5 rounded"
                style={{ background: "var(--accent)", color: "white" }}>
                Открыть гипотезу
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
