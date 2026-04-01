import { GroupedBarChart } from "@/components/charts/GroupedBarChart";
import type { ExperimentRecord } from "@/types/api";

interface AlgorithmComparisonChartProps {
  history: ExperimentRecord[];
}

export function AlgorithmComparisonChart({
  history,
}: AlgorithmComparisonChartProps) {
  if (history.length === 0) return null;

  const metricNames = [
    ...new Set(history.flatMap((r) => Object.keys(r.metrics))),
  ];
  if (metricNames.length === 0) return null;

  const chartData = history.map((r) => ({
    algorithm: r.algorithm,
    ...r.metrics,
  }));

  return (
    <GroupedBarChart
      title="Algorithm Comparison"
      data={chartData}
      xKey="algorithm"
      yKeys={metricNames}
    />
  );
}
