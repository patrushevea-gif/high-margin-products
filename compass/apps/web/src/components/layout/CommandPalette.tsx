"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";

interface Props {
  open: boolean;
  onClose: () => void;
}

const COMMANDS = [
  { label: "Mission Control", href: "/" },
  { label: "Список гипотез", href: "/hypotheses" },
  { label: "Создать гипотезу", href: "/hypotheses/new" },
  { label: "Источники данных", href: "/sources" },
  { label: "Карта процесса", href: "/process" },
  { label: "Агент-студия", href: "/agents" },
];

export function CommandPalette({ open, onClose }: Props) {
  const router = useRouter();

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        if (!open) onClose();
      }
      if (e.key === "Escape" && open) onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-24"
      style={{ background: "rgba(0,0,0,0.6)" }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-lg border overflow-hidden shadow-2xl"
        style={{ background: "var(--raised)", borderColor: "var(--border)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <Command>
          <div className="border-b" style={{ borderColor: "var(--border)" }}>
            <Command.Input
              placeholder="Поиск команд, гипотез, источников..."
              className="w-full px-4 py-3 text-sm outline-none"
              style={{ background: "transparent", color: "var(--text-primary)" }}
            />
          </div>
          <Command.List className="max-h-72 overflow-auto py-2">
            <Command.Empty className="px-4 py-3 text-sm" style={{ color: "var(--text-muted)" }}>
              Ничего не найдено
            </Command.Empty>
            {COMMANDS.map((cmd) => (
              <Command.Item
                key={cmd.href}
                onSelect={() => { router.push(cmd.href); onClose(); }}
                className="px-4 py-2.5 text-sm cursor-pointer flex items-center gap-2"
                style={{ color: "var(--text-primary)" }}
              >
                {cmd.label}
              </Command.Item>
            ))}
          </Command.List>
        </Command>
      </div>
    </div>
  );
}
