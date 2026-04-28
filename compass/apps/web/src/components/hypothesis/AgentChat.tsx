"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot } from "lucide-react";
import { cn } from "@/lib/utils";

const AGENTS = [
  { id: "synthesizer", label: "Синтезатор" },
  { id: "devils_advocate", label: "Адвокат Дьявола" },
  { id: "market_analyst", label: "Рыночный аналитик" },
  { id: "economist", label: "Экономист" },
  { id: "tech_analyst", label: "Технический аналитик" },
];

interface Message {
  role: "user" | "assistant";
  content: string;
  agent?: string;
}

interface Props {
  hypothesisId: string;
}

export function AgentChat({ hypothesisId }: Props) {
  const [agent, setAgent] = useState("synthesizer");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");

    const userMsg: Message = { role: "user", content: text };
    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    const assistantMsg: Message = { role: "assistant", content: "", agent };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
      const res = await fetch(`${apiBase}/api/v1/hypotheses/${hypothesisId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, agent, history }),
      });
      if (!res.body) throw new Error("No stream");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let full = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        full += decoder.decode(value, { stream: true });
        setMessages((prev) =>
          prev.map((m, i) => (i === prev.length - 1 ? { ...m, content: full } : m))
        );
      }
    } catch {
      setMessages((prev) =>
        prev.map((m, i) => (i === prev.length - 1 ? { ...m, content: "Ошибка соединения" } : m))
      );
    } finally {
      setLoading(false);
    }
  };

  const agentLabel = AGENTS.find((a) => a.id === agent)?.label ?? agent;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2.5 border-b"
        style={{ borderColor: "var(--border)" }}>
        <Bot size={13} style={{ color: "var(--accent)" }} />
        <select
          value={agent}
          onChange={(e) => setAgent(e.target.value)}
          className="flex-1 text-xs border-0 outline-none bg-transparent cursor-pointer"
          style={{ color: "var(--text-primary)" }}
        >
          {AGENTS.map((a) => (
            <option key={a.id} value={a.id} style={{ background: "var(--surface)" }}>
              {a.label}
            </option>
          ))}
        </select>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto px-3 py-2 space-y-3">
        {messages.length === 0 && (
          <div className="text-xs text-center mt-6" style={{ color: "var(--text-muted)" }}>
            Спроси {agentLabel}а о гипотезе
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={cn("flex gap-2", m.role === "user" ? "justify-end" : "justify-start")}>
            <div
              className="max-w-[85%] rounded px-2.5 py-2 text-xs leading-relaxed whitespace-pre-wrap"
              style={{
                background: m.role === "user" ? "var(--accent)" : "var(--surface)",
                color: m.role === "user" ? "white" : "var(--text-primary)",
                border: m.role === "assistant" ? "1px solid var(--border)" : "none",
              }}
            >
              {m.content || (loading && i === messages.length - 1
                ? <span className="animate-pulse" style={{ color: "var(--text-muted)" }}>...</span>
                : "")}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex items-center gap-2 px-3 py-2 border-t"
        style={{ borderColor: "var(--border)" }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Задай вопрос агенту..."
          disabled={loading}
          className="flex-1 text-xs px-2.5 py-1.5 rounded border outline-none focus:border-purple-500 disabled:opacity-50"
          style={{ background: "var(--background)", borderColor: "var(--border)", color: "var(--text-primary)" }}
        />
        <button
          onClick={send}
          disabled={!input.trim() || loading}
          className="p-1.5 rounded disabled:opacity-40 transition-colors"
          style={{ background: "var(--accent)", color: "white" }}
        >
          <Send size={13} />
        </button>
      </div>
    </div>
  );
}
