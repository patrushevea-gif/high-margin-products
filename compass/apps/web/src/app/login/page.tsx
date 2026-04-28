"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { toast } from "sonner";

export default function LoginPage() {
  const router = useRouter();
  const params = useSearchParams();
  const next = params.get("next") ?? "/";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    if (!supabase) {
      toast.error("Supabase не настроен");
      return;
    }
    setLoading(true);
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setLoading(false);
    if (error) {
      toast.error(error.message);
      return;
    }
    router.push(next);
    router.refresh();
  };

  return (
    <div className="min-h-screen flex items-center justify-center"
      style={{ background: "var(--background)" }}>
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex items-center gap-2.5 mb-8 justify-center">
          <div className="w-7 h-7 rounded" style={{ background: "var(--accent)" }} />
          <span className="text-lg font-semibold tracking-tight"
            style={{ color: "var(--text-primary)" }}>
            Compass
          </span>
        </div>

        <div className="rounded-lg border p-6"
          style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
          <h1 className="text-sm font-semibold mb-5" style={{ color: "var(--text-primary)" }}>
            Войти в систему
          </h1>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-medium mb-1.5"
                style={{ color: "var(--text-secondary)" }}>
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
                placeholder="you@company.ru"
                className="w-full px-3 py-2 rounded text-sm border outline-none focus:border-purple-500 transition-colors"
                style={{ background: "var(--background)", borderColor: "var(--border)",
                         color: "var(--text-primary)" }}
              />
            </div>

            <div>
              <label className="block text-xs font-medium mb-1.5"
                style={{ color: "var(--text-secondary)" }}>
                Пароль
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
                className="w-full px-3 py-2 rounded text-sm border outline-none focus:border-purple-500 transition-colors"
                style={{ background: "var(--background)", borderColor: "var(--border)",
                         color: "var(--text-primary)" }}
              />
            </div>

            <button
              type="submit"
              disabled={loading || !email || !password}
              className="w-full py-2 rounded text-sm font-medium disabled:opacity-40 transition-colors mt-2"
              style={{ background: "var(--accent)", color: "white" }}
            >
              {loading ? "Входим..." : "Войти"}
            </button>
          </form>

          <p className="text-xs text-center mt-4" style={{ color: "var(--text-muted)" }}>
            Нет аккаунта? Обратитесь к администратору
          </p>
        </div>
      </div>
    </div>
  );
}
