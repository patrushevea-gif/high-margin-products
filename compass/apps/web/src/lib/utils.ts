import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const STATUS_LABELS: Record<string, string> = {
  draft: "Черновик",
  signal_processed: "Сигнал обработан",
  tech_evaluated: "Техоценка",
  market_evaluated: "Рыночный анализ",
  economics_evaluated: "Экономика",
  compliance_checked: "Комплаенс",
  synthesized: "Синтезирован",
  challenged: "Проверен",
  committee_ready: "Готов к комитету",
  committee_decision: "Решение комитета",
  accepted: "Принят",
  rejected: "Отвергнут",
  parked: "Припаркован",
  to_review: "На пересмотре",
};

export const STATUS_COLORS: Record<string, string> = {
  draft: "text-text-muted",
  signal_processed: "text-info",
  tech_evaluated: "text-info",
  market_evaluated: "text-info",
  economics_evaluated: "text-info",
  compliance_checked: "text-info",
  synthesized: "text-accent",
  challenged: "text-warning",
  committee_ready: "text-success",
  committee_decision: "text-success",
  accepted: "text-success",
  rejected: "text-danger",
  parked: "text-text-muted",
  to_review: "text-warning",
};

export const DOMAIN_LABELS: Record<string, string> = {
  lkm: "ЛКМ",
  soj: "СОЖ",
  lubricants: "Смазочные материалы",
  anticor: "Антикоррозийные",
  sealants: "Герметики",
  adhesives: "Адгезивы",
  specialty: "Спецхимия",
  reagents: "Реагенты",
  additives: "Добавки",
  surfactants: "ПАВ",
};

export function formatCost(usd: number): string {
  return `$${usd.toFixed(4)}`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("ru-RU", {
    day: "2-digit", month: "short", year: "numeric",
  });
}
