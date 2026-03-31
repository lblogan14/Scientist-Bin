import { MetricScatterChart } from "@/components/charts/MetricScatterChart";
import type { Experiment, ExperimentRecord } from "@/types/api";

interface ModelTradeoffScatterProps {
  models: Experiment[];
}

export function ModelTradeoffScatter({ models }: ModelTradeoffScatterProps) {
  // Flatten all experiment histories
  const allRecords: (ExperimentRecord & { objective: string })[] = [];
  for (const model of models) {
    for (const record of model.result?.experiment_history ?? []) {
      allRecords.push({ ...record, objective: model.objective });
    }
  }

  // Find the primary metric (first available)
  const firstRecord = allRecords[0];
  if (!firstRecord) return null;
  const primaryMetric = Object.keys(firstRecord.metrics)[0];
  if (!primaryMetric) return null;

  const scatterData = allRecords
    .filter(
      (r) =>
        r.metrics[primaryMetric] != null && r.training_time_seconds != null,
    )
    .map((r) => ({
      name: r.algorithm,
      x: Math.round(r.training_time_seconds * 100) / 100,
      y: r.metrics[primaryMetric]!,
    }));

  if (scatterData.length === 0) return null;

  return (
    <MetricScatterChart
      title={`${primaryMetric} vs Training Time`}
      data={scatterData}
      xLabel="Training Time (s)"
      yLabel={primaryMetric}
    />
  );
}
