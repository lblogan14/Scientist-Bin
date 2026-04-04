import { useState } from "react";
import { AlertTriangle, Boxes } from "lucide-react";
import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";
import { ExperimentSelector } from "@/components/shared/ExperimentSelector";
import { useExperimentIdSync } from "@/hooks/use-experiment-id-sync";
import type { ExperimentResult } from "@/types/api";
import { isExperimentError } from "@/types/api";
import { useModels } from "../hooks/use-models";
import { DeploymentCard } from "./DeploymentCard";
import { ModelComparisonTable } from "./ModelComparisonTable";
import { ModelMetricChart } from "./ModelMetricChart";
import { ModelRankingCard } from "./ModelRankingCard";
import { ModelTradeoffScatter } from "./ModelTradeoffScatter";

export default function ModelSelectionPage() {
  const { experimentId, setExperimentId } = useExperimentIdSync();
  const { data: models, isLoading, isError } = useModels(experimentId);
  const [deployedModelId, setDeployedModelId] = useState<string | null>(null);

  if (isLoading) return <LoadingSpinner message="Loading models..." />;
  if (isError) {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="Failed to load models"
        description="Could not fetch experiments. Check that the backend is running."
      />
    );
  }

  // Find the best model for deployment
  const bestModel = models?.find((m) => {
    if (!m.result || isExperimentError(m.result)) return false;
    return true;
  });
  const bestResult = bestModel?.result as ExperimentResult | undefined;
  const activeDeployId = deployedModelId ?? bestModel?.id ?? null;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <h2 className="text-2xl font-bold">Models</h2>
        <ExperimentSelector
          statusFilter={["completed"]}
          showAllOption
          value={experimentId ?? "all"}
          onChange={(id) => setExperimentId(id === "all" ? null : id)}
          className="w-64"
        />
      </div>
      {!models || models.length === 0 ? (
        <EmptyState
          icon={Boxes}
          title="No completed models"
          description="Complete a training experiment to see models here."
        />
      ) : (
        <>
          {/* Deployment section */}
          {activeDeployId && bestResult && (
            <DeploymentCard
              experimentId={activeDeployId}
              modelName={bestResult.best_model ?? "Best Model"}
            />
          )}

          <ModelRankingCard
            models={models}
            onDeployClick={(id) => setDeployedModelId(id)}
          />
          <div className="grid gap-4 md:grid-cols-2">
            <ModelMetricChart models={models} />
            <ModelTradeoffScatter models={models} />
          </div>
          <ModelComparisonTable models={models} />
        </>
      )}
    </div>
  );
}
