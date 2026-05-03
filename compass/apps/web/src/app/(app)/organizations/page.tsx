"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useOrg } from "@/lib/org-context";
import { toast } from "sonner";
import { Building2, UserPlus, Shield, Trash2, Crown, Eye, FlaskConical } from "lucide-react";

interface OrgMember {
  id: string;
  user_id: string;
  email: string;
  role: string;
  accepted_at: string | null;
  created_at: string;
}

interface OrgContext {
  org_id: string;
  name: string;
  slug: string;
  plan: string;
  role: string;
  members_count: number;
  hypotheses_limit: number;
}

interface AuditEntry {
  id: string;
  email: string;
  action: string;
  resource_type: string | null;
  created_at: string;
  meta: Record<string, unknown>;
}

const ROLE_ICONS: Record<string, React.ReactNode> = {
  owner:      <Crown size={12} />,
  admin:      <Shield size={12} />,
  researcher: <FlaskConical size={12} />,
  viewer:     <Eye size={12} />,
};

const ROLE_COLORS: Record<string, string> = {
  owner:      "#f59e0b",
  admin:      "#7c3aed",
  researcher: "#3b82f6",
  viewer:     "#64748b",
};

const PLAN_LABELS: Record<string, string> = {
  starter:      "Starter",
  professional: "Professional",
  enterprise:   "Enterprise",
};

export default function OrganizationsPage() {
  const { orgId, orgName, orgRole } = useOrg();
  const qc = useQueryClient();
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("researcher");
  const [showCreate, setShowCreate] = useState(false);
  const [newOrgName, setNewOrgName] = useState("");
  const [activeTab, setActiveTab] = useState<"members" | "audit">("members");

  const { data: ctx } = useQuery<OrgContext>({
    queryKey: ["org-context"],
    queryFn: () => api.get<OrgContext>("/organizations/context"),
    enabled: !!orgId,
  });

  const { data: members = [] } = useQuery<OrgMember[]>({
    queryKey: ["org-members", orgId],
    queryFn: () => api.get<OrgMember[]>(`/organizations/${orgId}/members`),
    enabled: !!orgId,
  });

  const { data: auditLog = [] } = useQuery<AuditEntry[]>({
    queryKey: ["org-audit", orgId],
    queryFn: () => api.get<AuditEntry[]>(`/organizations/${orgId}/audit-log?limit=50`),
    enabled: !!orgId && activeTab === "audit",
  });

  const inviteMutation = useMutation({
    mutationFn: () =>
      api.post(`/organizations/${orgId}/invite`, { email: inviteEmail, role: inviteRole }),
    onSuccess: () => {
      toast.success(`Приглашение отправлено на ${inviteEmail}`);
      setInviteEmail("");
      qc.invalidateQueries({ queryKey: ["org-members"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const removesMutation = useMutation({
    mutationFn: (memberId: string) =>
      api.delete(`/organizations/${orgId}/members/${memberId}`),
    onSuccess: () => {
      toast.success("Участник удалён");
      qc.invalidateQueries({ queryKey: ["org-members"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const changeRoleMutation = useMutation({
    mutationFn: ({ memberId, role }: { memberId: string; role: string }) =>
      api.patch(`/organizations/${orgId}/members/${memberId}/role`, { role }),
    onSuccess: () => {
      toast.success("Роль обновлена");
      qc.invalidateQueries({ queryKey: ["org-members"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const createOrgMutation = useMutation({
    mutationFn: () => api.post("/organizations", { name: newOrgName }),
    onSuccess: () => {
      toast.success("Организация создана");
      setShowCreate(false);
      setNewOrgName("");
      qc.invalidateQueries({ queryKey: ["my-orgs"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const canManage = orgRole === "admin" || orgRole === "owner";

  return (
    <div className="p-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center"
            style={{ background: "rgba(124,58,237,0.12)" }}>
            <Building2 size={18} style={{ color: "var(--accent)" }} />
          </div>
          <div>
            <h1 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>
              {orgName ?? "Организация"}
            </h1>
            {ctx && (
              <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                {PLAN_LABELS[ctx.plan] ?? ctx.plan} · {ctx.members_count} участников ·
                {" "}{ctx.hypotheses_limit} гипотез/год
              </p>
            )}
          </div>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium border transition-colors"
          style={{ borderColor: "var(--border)", color: "var(--text-secondary)", background: "var(--raised)" }}
        >
          <Building2 size={12} />
          Новая организация
        </button>
      </div>

      {/* Create org modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="rounded-xl border p-6 w-96"
            style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
            <h2 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
              Создать организацию
            </h2>
            <input
              value={newOrgName}
              onChange={(e) => setNewOrgName(e.target.value)}
              placeholder="Название компании"
              className="w-full px-3 py-2 rounded border text-sm mb-4"
              style={{ background: "var(--raised)", borderColor: "var(--border)", color: "var(--text-primary)" }}
            />
            <div className="flex gap-2">
              <button
                onClick={() => createOrgMutation.mutate()}
                disabled={!newOrgName || createOrgMutation.isPending}
                className="flex-1 py-2 rounded text-sm font-medium"
                style={{ background: "var(--accent)", color: "white" }}
              >
                {createOrgMutation.isPending ? "Создание..." : "Создать"}
              </button>
              <button
                onClick={() => setShowCreate(false)}
                className="px-4 py-2 rounded text-sm border"
                style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-5 border-b" style={{ borderColor: "var(--border)" }}>
        {(["members", "audit"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className="px-4 py-2 text-sm -mb-px border-b-2 transition-colors"
            style={{
              borderColor: activeTab === tab ? "var(--accent)" : "transparent",
              color: activeTab === tab ? "var(--accent)" : "var(--text-muted)",
            }}
          >
            {tab === "members" ? "Участники" : "Audit Log"}
          </button>
        ))}
      </div>

      {activeTab === "members" && (
        <>
          {/* Invite form */}
          {canManage && (
            <div className="rounded-lg border p-4 mb-5"
              style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
              <p className="text-xs font-medium mb-3" style={{ color: "var(--text-muted)" }}>
                Пригласить участника
              </p>
              <div className="flex gap-2">
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="email@company.com"
                  className="flex-1 px-3 py-2 rounded border text-sm"
                  style={{ background: "var(--raised)", borderColor: "var(--border)", color: "var(--text-primary)" }}
                />
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="px-3 py-2 rounded border text-sm"
                  style={{ background: "var(--raised)", borderColor: "var(--border)", color: "var(--text-primary)" }}
                >
                  <option value="viewer">Viewer</option>
                  <option value="researcher">Researcher</option>
                  <option value="admin">Admin</option>
                </select>
                <button
                  onClick={() => inviteMutation.mutate()}
                  disabled={!inviteEmail || inviteMutation.isPending}
                  className="flex items-center gap-1.5 px-4 py-2 rounded text-sm font-medium"
                  style={{ background: "var(--accent)", color: "white" }}
                >
                  <UserPlus size={14} />
                  {inviteMutation.isPending ? "..." : "Пригласить"}
                </button>
              </div>
            </div>
          )}

          {/* Members list */}
          <div className="rounded-lg border overflow-hidden"
            style={{ borderColor: "var(--border)" }}>
            <table className="w-full text-sm">
              <thead>
                <tr style={{ background: "var(--surface)", borderBottom: "1px solid var(--border)" }}>
                  <th className="text-left px-4 py-2.5 text-xs font-medium"
                    style={{ color: "var(--text-muted)" }}>Email</th>
                  <th className="text-left px-4 py-2.5 text-xs font-medium"
                    style={{ color: "var(--text-muted)" }}>Роль</th>
                  <th className="text-left px-4 py-2.5 text-xs font-medium"
                    style={{ color: "var(--text-muted)" }}>Статус</th>
                  {canManage && (
                    <th className="text-right px-4 py-2.5 text-xs font-medium"
                      style={{ color: "var(--text-muted)" }}>Действия</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {members.map((m) => (
                  <tr key={m.id} className="border-t"
                    style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
                    <td className="px-4 py-3" style={{ color: "var(--text-primary)" }}>
                      {m.email}
                    </td>
                    <td className="px-4 py-3">
                      {canManage && m.role !== "owner" ? (
                        <select
                          value={m.role}
                          onChange={(e) => changeRoleMutation.mutate({ memberId: m.id, role: e.target.value })}
                          className="px-2 py-1 rounded border text-xs"
                          style={{ background: "var(--raised)", borderColor: "var(--border)", color: ROLE_COLORS[m.role] }}
                        >
                          <option value="viewer">Viewer</option>
                          <option value="researcher">Researcher</option>
                          <option value="admin">Admin</option>
                        </select>
                      ) : (
                        <span className="flex items-center gap-1 text-xs"
                          style={{ color: ROLE_COLORS[m.role] }}>
                          {ROLE_ICONS[m.role]}
                          {m.role}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs px-2 py-0.5 rounded"
                        style={{
                          background: m.accepted_at ? "rgba(16,185,129,0.1)" : "rgba(245,158,11,0.1)",
                          color: m.accepted_at ? "#10b981" : "#f59e0b",
                        }}>
                        {m.accepted_at ? "Активен" : "Ожидает"}
                      </span>
                    </td>
                    {canManage && (
                      <td className="px-4 py-3 text-right">
                        {m.role !== "owner" && (
                          <button
                            onClick={() => removesMutation.mutate(m.id)}
                            disabled={removesMutation.isPending}
                            className="p-1.5 rounded transition-colors hover:bg-red-500/10"
                            style={{ color: "var(--text-muted)" }}
                          >
                            <Trash2 size={13} />
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>

            {members.length === 0 && (
              <div className="px-4 py-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>
                Нет участников
              </div>
            )}
          </div>
        </>
      )}

      {activeTab === "audit" && (
        <div className="rounded-lg border overflow-hidden" style={{ borderColor: "var(--border)" }}>
          <table className="w-full text-sm">
            <thead>
              <tr style={{ background: "var(--surface)", borderBottom: "1px solid var(--border)" }}>
                <th className="text-left px-4 py-2.5 text-xs font-medium" style={{ color: "var(--text-muted)" }}>Время</th>
                <th className="text-left px-4 py-2.5 text-xs font-medium" style={{ color: "var(--text-muted)" }}>Пользователь</th>
                <th className="text-left px-4 py-2.5 text-xs font-medium" style={{ color: "var(--text-muted)" }}>Действие</th>
                <th className="text-left px-4 py-2.5 text-xs font-medium" style={{ color: "var(--text-muted)" }}>Ресурс</th>
              </tr>
            </thead>
            <tbody>
              {auditLog.map((entry) => (
                <tr key={entry.id} className="border-t"
                  style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
                  <td className="px-4 py-2.5 text-xs" style={{ color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                    {new Date(entry.created_at).toLocaleString("ru-RU", {
                      month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"
                    })}
                  </td>
                  <td className="px-4 py-2.5 text-xs" style={{ color: "var(--text-secondary)" }}>
                    {entry.email}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="text-xs px-2 py-0.5 rounded font-mono"
                      style={{ background: "var(--raised)", color: "var(--text-primary)" }}>
                      {entry.action}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-xs" style={{ color: "var(--text-muted)" }}>
                    {entry.resource_type}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {auditLog.length === 0 && (
            <div className="px-4 py-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>
              Нет записей
            </div>
          )}
        </div>
      )}
    </div>
  );
}
