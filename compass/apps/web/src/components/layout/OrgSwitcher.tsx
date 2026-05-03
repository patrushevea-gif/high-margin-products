"use client";

import { useState, useRef, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useOrg } from "@/lib/org-context";
import { Building2, ChevronDown, Plus, Check } from "lucide-react";

interface OrgItem {
  id: string;
  name: string;
  slug: string;
  plan: string;
}

interface OrgMembership extends OrgItem {
  role: string;
}

export function OrgSwitcher() {
  const { orgId, orgName, orgRole, setOrg } = useOrg();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const { data: orgs = [] } = useQuery<OrgItem[]>({
    queryKey: ["my-orgs"],
    queryFn: () => api.get<OrgItem[]>("/organizations"),
    staleTime: 60_000,
  });

  // Auto-select first org if none selected
  useEffect(() => {
    if (!orgId && orgs.length > 0) {
      setOrg(orgs[0].id, orgs[0].name, "researcher");
    }
  }, [orgs, orgId, setOrg]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  if (orgs.length === 0 && !orgId) return null;

  const planBadge: Record<string, string> = {
    starter: "S",
    professional: "P",
    enterprise: "E",
  };

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 px-2.5 py-2 rounded text-sm transition-colors hover:bg-background-raised"
        style={{ color: "var(--text-secondary)" }}
      >
        <Building2 size={14} strokeWidth={1.5} style={{ color: "var(--accent)", flexShrink: 0 }} />
        <span className="flex-1 text-left truncate text-xs font-medium"
          style={{ color: "var(--text-primary)" }}>
          {orgName ?? "Организация"}
        </span>
        {orgRole && (
          <span className="text-xs px-1 py-0.5 rounded"
            style={{ background: "rgba(124,58,237,0.12)", color: "var(--accent)", fontSize: 9 }}>
            {orgRole}
          </span>
        )}
        <ChevronDown size={12} style={{ color: "var(--text-muted)", flexShrink: 0 }} />
      </button>

      {open && (
        <div
          className="absolute left-0 bottom-full mb-1 w-56 rounded-lg border shadow-xl z-50"
          style={{ background: "var(--surface)", borderColor: "var(--border)" }}
        >
          <div className="px-3 py-2 border-b text-xs font-medium"
            style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}>
            Организации
          </div>

          <div className="py-1 max-h-48 overflow-auto">
            {orgs.map((org) => (
              <button
                key={org.id}
                onClick={() => {
                  setOrg(org.id, org.name, "researcher");
                  setOpen(false);
                  window.location.reload();
                }}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-left transition-colors hover:bg-background-raised"
                style={{ color: "var(--text-primary)" }}
              >
                <span
                  className="w-6 h-6 rounded flex items-center justify-center text-xs font-bold flex-shrink-0"
                  style={{ background: "rgba(124,58,237,0.15)", color: "var(--accent)" }}
                >
                  {planBadge[org.plan] ?? org.name[0].toUpperCase()}
                </span>
                <span className="flex-1 truncate">{org.name}</span>
                {org.id === orgId && (
                  <Check size={12} style={{ color: "var(--accent)" }} />
                )}
              </button>
            ))}
          </div>

          <div className="border-t py-1" style={{ borderColor: "var(--border)" }}>
            <a
              href="/organizations"
              className="flex items-center gap-2 px-3 py-2 text-xs transition-colors hover:bg-background-raised"
              style={{ color: "var(--text-muted)" }}
              onClick={() => setOpen(false)}
            >
              <Plus size={12} />
              Управление организацией
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
