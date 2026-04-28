import { HypothesisWorkbench } from "@/components/hypothesis/HypothesisWorkbench";

export default async function HypothesisPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <HypothesisWorkbench id={id} />;
}
