"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { DOMAIN_LABELS } from "@/lib/utils";
import { toast } from "sonner";

const DOMAINS = Object.entries(DOMAIN_LABELS);

export default function NewHypothesisPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    title: "",
    short_description: "",
    long_description: "",
    domain: "lkm",
  });

  const mutation = useMutation({
    mutationFn: () => api.post("/hypotheses", form),
    onSuccess: (data: any) => {
      toast.success("Гипотеза создана");
      router.push(`/hypotheses/${data.id}`);
    },
    onError: () => toast.error("Ошибка при создании гипотезы"),
  });

  const set = (k: string, v: string) => setForm((f: typeof form) => ({ ...f, [k]: v }));

  const valid = form.title.trim().length >= 5 && form.short_description.trim().length >= 10;

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      <div className="mb-6">
        <h1 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>
          Новая гипотеза
        </h1>
        <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
          Заполните базовые поля — агенты проведут детальную оценку автоматически
        </p>
      </div>

      <div className="rounded-lg border p-5 space-y-4"
        style={{ borderColor: "var(--border)", background: "var(--surface)" }}>

        {/* Title */}
        <div>
          <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>
            Заголовок *
          </label>
          <input
            value={form.title}
            onChange={(e) => set("title", e.target.value)}
            placeholder="Например: Водно-дисперсионные краски для арктического климата"
            className="w-full px-3 py-2 rounded text-sm border outline-none focus:border-purple-500 transition-colors"
            style={{ background: "var(--background)", borderColor: "var(--border)", color: "var(--text-primary)" }}
          />
        </div>

        {/* Domain */}
        <div>
          <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>
            Домен *
          </label>
          <select
            value={form.domain}
            onChange={(e) => set("domain", e.target.value)}
            className="w-full px-3 py-2 rounded text-sm border outline-none focus:border-purple-500 transition-colors"
            style={{ background: "var(--background)", borderColor: "var(--border)", color: "var(--text-primary)" }}
          >
            {DOMAINS.map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>
        </div>

        {/* Short description */}
        <div>
          <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>
            Краткое описание * <span className="font-normal" style={{ color: "var(--text-muted)" }}>(1–2 предложения)</span>
          </label>
          <textarea
            value={form.short_description}
            onChange={(e) => set("short_description", e.target.value)}
            rows={3}
            placeholder="В чём суть гипотезы и потенциальный рынок?"
            className="w-full px-3 py-2 rounded text-sm border outline-none focus:border-purple-500 transition-colors resize-none"
            style={{ background: "var(--background)", borderColor: "var(--border)", color: "var(--text-primary)" }}
          />
        </div>

        {/* Long description */}
        <div>
          <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>
            Подробное описание <span className="font-normal" style={{ color: "var(--text-muted)" }}>(опционально)</span>
          </label>
          <textarea
            value={form.long_description}
            onChange={(e) => set("long_description", e.target.value)}
            rows={6}
            placeholder="Технология, целевые сегменты, известные конкуренты, источники идеи..."
            className="w-full px-3 py-2 rounded text-sm border outline-none focus:border-purple-500 transition-colors resize-none"
            style={{ background: "var(--background)", borderColor: "var(--border)", color: "var(--text-primary)" }}
          />
        </div>
      </div>

      <div className="flex items-center justify-between mt-5">
        <button
          onClick={() => router.back()}
          className="px-4 py-2 rounded text-sm border transition-colors"
          style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
        >
          Отмена
        </button>
        <div className="flex items-center gap-3">
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            После создания запустится полный агентский пайплайн
          </p>
          <button
            disabled={!valid || mutation.isPending}
            onClick={() => mutation.mutate()}
            className="px-5 py-2 rounded text-sm font-medium transition-colors disabled:opacity-40"
            style={{ background: "var(--accent)", color: "white" }}
          >
            {mutation.isPending ? "Создание..." : "Создать гипотезу"}
          </button>
        </div>
      </div>
    </div>
  );
}
