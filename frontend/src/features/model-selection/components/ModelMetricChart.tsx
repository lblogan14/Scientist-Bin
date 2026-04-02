import { GroupedBarChart } from "@/components/charts/GroupedBarChart";
import {
  type Experiment,
  type ExperimentRecord,
  isExperimentError,
} from "@/types/api";

interface ModelMetricChartProps {
  models: Experiment[];
}

export function ModelMetricChart({ models }: ModelMetricChartProps) {
  if (models.length === 0) return null;

  // Extract best record from each experiment
  const chartData: Record<string, unknown>[] = [];
  const allMetricNames = new Set<string>();

  for (const model of models) {
    const r = model.result;
    const history: ExperimentRecord[] =
      r && !isExperimentError(r) ? (r.experiment_history ?? []) : [];
    if (history.length === 0) continue;

    // Find best record by first metric value
    const best = history.reduce((a: ExperimentRecord, b: ExperimentRecord) => {
      const aVal = Object.values(a.metrics)[0] ?? 0;
      const bVal = Object.values(b.metrics)[0] ?? 0;
      return bVal > aVal ? b : a;
    });

    for (const key of Object.keys(best.metrics)) {
      allMetricNames.add(key);
    }

    const label =
      model.objective.length > 20
        ? model.objective.slice(0, 20) + "..."
        : model.objective;

    chartData.push({ experiment: label, ...best.metrics });
  }

  const metricNames = [...allMetricNames].slice(0, 4);
  if (chartData.length === 0 || metricNames.length === 0) return null;

  return (
    <GroupedBarChart
      title="Best Metrics by Experiment"
      data={chartData}
      xKey="experiment"
      yKeys={metricNames}
    />
  );
}
