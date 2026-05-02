import { Suspense } from "react";
import { HypothesisList } from "@/components/hypothesis/HypothesisList";

export default function HypothesesPage() {
  return (
    <Suspense fallback={<div className="p-5 space-y-2">{Array.from({ length: 8 }).map((_, i) => <div key={i} className="h-10 rounded animate-pulse" style={{ background: "var(--surface)" }} />)}</div>}>
      <HypothesisList />
    </Suspense>
  );
}
