"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, FlaskConical, Radio, Settings, Database,
  GitBranch, Search, Bell
} from "lucide-react";
import { CommandPalette } from "@/components/layout/CommandPalette";
import { useState } from "react";

const NAV = [
  { href: "/", label: "Mission Control", icon: LayoutDashboard },
  { href: "/hypotheses", label: "Гипотезы", icon: FlaskConical },
  { href: "/sources", label: "Источники", icon: Database },
  { href: "/process", label: "Карта процесса", icon: GitBranch },
  { href: "/agents", label: "Агент-студия", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [cmdOpen, setCmdOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: "var(--background)" }}>
      {/* Sidebar */}
      <aside
        className="flex flex-col w-52 border-r flex-shrink-0"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        {/* Logo */}
        <div className="px-4 py-4 border-b" style={{ borderColor: "var(--border)" }}>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded" style={{ background: "var(--accent)" }} />
            <span className="font-semibold text-sm tracking-tight" style={{ color: "var(--text-primary)" }}>
              Compass
            </span>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-2 py-3 space-y-0.5">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-2.5 px-2.5 py-2 rounded text-sm transition-colors",
                  active
                    ? "text-accent font-medium"
                    : "hover:bg-background-raised",
                )}
                style={{
                  color: active ? "var(--accent)" : "var(--text-secondary)",
                  background: active ? "rgba(124,58,237,0.08)" : undefined,
                }}
              >
                <Icon size={15} strokeWidth={1.5} />
                {label}
              </Link>
            );
          })}
        </nav>

        {/* Bottom */}
        <div className="px-2 py-3 border-t" style={{ borderColor: "var(--border)" }}>
          <button
            onClick={() => setCmdOpen(true)}
            className="flex items-center gap-2 px-2.5 py-2 rounded text-sm w-full transition-colors hover:bg-background-raised"
            style={{ color: "var(--text-muted)" }}
          >
            <Search size={14} strokeWidth={1.5} />
            <span>Поиск</span>
            <kbd className="ml-auto text-xs px-1 py-0.5 rounded" style={{ background: "var(--raised)", color: "var(--text-muted)" }}>
              ⌘K
            </kbd>
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>

      <CommandPalette open={cmdOpen} onClose={() => setCmdOpen(false)} />
    </div>
  );
}
