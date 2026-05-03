import { getOrgId } from "@/lib/org-context";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function buildHeaders(extra?: HeadersInit): HeadersInit {
  const orgId = getOrgId();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (orgId) headers["X-Organization-Id"] = orgId;
  return { ...headers, ...(extra as Record<string, string> | undefined) };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}/api/v1${path}`, {
    ...init,
    headers: buildHeaders(init?.headers),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API error ${res.status}: ${err}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: (path: string) => request<void>(path, { method: "DELETE" }),
};
