import { HypothesisWorkbench } from "@/components/hypothesis/HypothesisWorkbench";

export default function HypothesisPage({ params }: { params: { id: string } }) {
  return <HypothesisWorkbench id={params.id} />;
}
