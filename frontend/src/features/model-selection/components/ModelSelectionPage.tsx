import { Boxes } from "lucide-react";
import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";
import { useModels } from "../hooks/use-models";
import { ModelComparisonTable } from "./ModelComparisonTable";

export default function ModelSelectionPage() {
  const { data: models, isLoading } = useModels();

  if (isLoading) return <LoadingSpinner message="Loading models..." />;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Models</h2>
      {!models || models.length === 0 ? (
        <EmptyState
          icon={Boxes}
          title="No completed models"
          description="Complete a training experiment to see models here."
        />
      ) : (
        <ModelComparisonTable models={models} />
      )}
    </div>
  );
}
