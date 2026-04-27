"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { AgentSettings } from "@/types";
import { toast } from "sonner";

const MODE_PRESETS = {
  conservative: { label: "Conservative", description: "Низкие температуры, строгий отсев" },
  balanced: { label: "Balanced", description: "Сбалансированные настройки (по умолчанию)" },
  explorer: { label: "Explorer", description: "Высокие температуры, широкий охват" },
  maverick: { label: "Maverick", description: "Максимальный поиск, для брейнштормов" },
};

export function AgentStudio() {
  const qc = useQueryClient();
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [editedPrompt, setEditedPrompt] = useState("");
  const [editedTemp, setEditedTemp] = useState(0.3);
  const [editedModel, setEditedModel] = useState("");
  const [editedMaxTokens, setEditedMaxTokens] = useState(4096);
  const [editedAutoConfirm, setEditedAutoConfirm] = useState(false);

  const { data: agents = [] } = useQuery<AgentSettings[]>({
    queryKey: ["agent-settings"],
    queryFn: () => api.get<AgentSettings[]>("/agents/settings"),
  });

  const selected = agents.find((a) => a.agent_name === selectedAgent);

  const handleSelect = (a: AgentSettings) => {
    setSelectedAgent(a.agent_name);
    setEditedPrompt(a.system_prompt);
    setEditedTemp(a.temperature);
    setEditedModel(a.model);
    setEditedMaxTokens(a.max_tokens);
    setEditedAutoConfirm(a.auto_confirm);
  };

  const saveMutation = useMutation({
    mutationFn: () =>
      api.patch(`/agents/settings/${selectedAgent}`, {
        system_prompt: editedPrompt !== selected?.system_prompt ? editedPrompt : undefined,
        temperature: editedTemp,
        model: editedModel,
        max_tokens: editedMaxTokens,
        auto_confirm: editedAutoConfirm,
      }),
    onSuccess: () => {
      toast.success("Настройки агента сохранены");
      qc.invalidateQueries({ queryKey: ["agent-settings"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="flex h-full">
      {/* Left: agent list */}
      <div
        className="w-56 flex-shrink-0 border-r overflow-auto"
        style={{ borderColor: "var(--border)", background: "var(--surface)" }}
      >
        <div
          className="px-3 py-2.5 text-xs font-medium border-b"
          style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}
        >
          Агенты
        </div>

        {/* Mode presets */}
        <div className="px-3 py-2 border-b" style={{ borderColor: "var(--border)" }}>
          <p className="text-xs mb-1.5" style={{ color: "var(--text-muted)" }}>Режим мышления</p>
          <div className="grid grid-cols-2 gap-1">
            {Object.entries(MODE_PRESETS).map(([key, preset]) => (
              <button
                key={key}
                className="text-xs px-2 py-1 rounded border hover:bg-background-raised transition-colors text-left"
                style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
                onClick={() => toast.info(`Пресет "${preset.label}" — в разработке`)}
                title={preset.description}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        {agents.map((a) => (
          <button
            key={a.agent_name}
            onClick={() => handleSelect(a)}
            className="w-full text-left px-3 py-2.5 border-b text-sm transition-colors"
            style={{
              borderColor: "var(--border)",
              background: selectedAgent === a.agent_name ? "rgba(124,58,237,0.08)" : "transparent",
              color: selectedAgent === a.agent_name ? "var(--accent)" : "var(--text-primary)",
            }}
          >
            <div className="font-medium text-xs">{a.display_name}</div>
            <div className="text-xs mt-0.5 truncate" style={{ color: "var(--text-muted)" }}>
              {a.model.replace("claude-", "")} · t={a.temperature}
            </div>
          </button>
        ))}
      </div>

      {/* Right: settings form */}
      <div className="flex-1 overflow-auto">
        {!selected ? (
          <div className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>
            Выберите агента для редактирования
          </div>
        ) : (
          <div className="p-5 max-w-2xl">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>
                  {selected.display_name}
                </h2>
                <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                  {selected.description}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                  v{selected.system_prompt_version}
                </span>
                <button
                  onClick={() => saveMutation.mutate()}
                  disabled={saveMutation.isPending}
                  className="px-3 py-1.5 rounded text-sm"
                  style={{ background: "var(--accent)", color: "white" }}
                >
                  {saveMutation.isPending ? "Сохранение..." : "Сохранить"}
                </button>
              </div>
            </div>

            {/* Model */}
            <div className="mb-4">
              <label className="text-xs font-medium block mb-1.5" style={{ color: "var(--text-muted)" }}>
                Модель
              </label>
              <select
                value={editedModel}
                onChange={(e) => setEditedModel(e.target.value)}
                className="w-full px-3 py-2 rounded border text-sm"
                style={{
                  background: "var(--raised)",
                  borderColor: "var(--border)",
                  color: "var(--text-primary)",
                }}
              >
                <option value="claude-sonnet-4-6">claude-sonnet-4-6</option>
                <option value="claude-opus-4-7">claude-opus-4-7</option>
                <option value="claude-haiku-4-5-20251001">claude-haiku-4-5-20251001</option>
              </select>
            </div>

            {/* Temperature */}
            <div className="mb-4">
              <label className="text-xs font-medium block mb-1.5" style={{ color: "var(--text-muted)" }}>
                Temperature: {editedTemp}
              </label>
              <input
                type="range" min={0} max={1} step={0.05}
                value={editedTemp}
                onChange={(e) => setEditedTemp(parseFloat(e.target.value))}
                className="w-full accent-purple-600"
              />
              <div className="flex justify-between text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                <span>0 (точный)</span>
                <span>1 (творческий)</span>
              </div>
            </div>

            {/* Max tokens */}
            <div className="mb-4">
              <label className="text-xs font-medium block mb-1.5" style={{ color: "var(--text-muted)" }}>
                Max tokens: {editedMaxTokens}
              </label>
              <input
                type="range" min={256} max={32768} step={256}
                value={editedMaxTokens}
                onChange={(e) => setEditedMaxTokens(parseInt(e.target.value))}
                className="w-full accent-purple-600"
              />
            </div>

            {/* Auto-confirm */}
            <div className="mb-4 flex items-center gap-2">
              <input
                type="checkbox"
                id="auto-confirm"
                checked={editedAutoConfirm}
                onChange={(e) => setEditedAutoConfirm(e.target.checked)}
                className="accent-purple-600"
              />
              <label htmlFor="auto-confirm" className="text-sm" style={{ color: "var(--text-primary)" }}>
                Автономный режим (без подтверждения человека)
              </label>
            </div>

            {/* Allowed tools */}
            {selected.allowed_tools.length > 0 && (
              <div className="mb-4">
                <label className="text-xs font-medium block mb-1.5" style={{ color: "var(--text-muted)" }}>
                  Инструменты
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {selected.allowed_tools.map((t) => (
                    <span key={t} className="text-xs px-2 py-0.5 rounded"
                      style={{ background: "var(--raised)", color: "var(--text-secondary)" }}>
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* System prompt */}
            <div className="mb-4">
              <label className="text-xs font-medium block mb-1.5" style={{ color: "var(--text-muted)" }}>
                System Prompt (версия {selected.system_prompt_version})
              </label>
              <textarea
                value={editedPrompt}
                onChange={(e) => setEditedPrompt(e.target.value)}
                rows={12}
                className="w-full px-3 py-2 rounded border text-xs resize-y"
                style={{
                  background: "var(--raised)",
                  borderColor: "var(--border)",
                  color: "var(--text-primary)",
                  fontFamily: "JetBrains Mono, monospace",
                  lineHeight: "1.6",
                }}
              />
              <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                Изменение промпта создаст новую версию. Старые версии сохраняются.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
