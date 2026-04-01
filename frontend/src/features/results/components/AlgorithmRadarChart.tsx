import { MetricRadarChart } from "@/components/charts/MetricRadarChart";
import type { ExperimentRecord } from "@/types/api";

interface AlgorithmRadarChartProps {
  history: ExperimentRecord[];
}

export function AlgorithmRadarChart({ history }: AlgorithmRadarChartProps) {
  if (history.length < 3) return null;

  const metricNames = [
    ...new Set(history.flatMap((r) => Object.keys(r.metrics))),
  ];
  if (metricNames.length < 2) return null;

  const algorithms = history.map((r) => r.algorithm);

  // Normalize metrics to 0-1 range per metric for radar readability
  const ranges = metricNames.map((metric) => {
    const values = history.map((r) => r.metrics[metric] ?? 0);
    const min = Math.min(...values);
    const max = Math.max(...values);
    return { metric, min, max };
  });

  const data = ranges.map(({ metric, min, max }) => {
    const row: { metric: string; [key: string]: string | number } = { metric };
    for (const record of history) {
      const raw = record.metrics[metric] ?? 0;
      // Normalize: if all values are same, set to 1
      row[record.algorithm] = max === min ? 1 : (raw - min) / (max - min);
    }
    return row;
  });

  return (
    <MetricRadarChart
      title="Multi-Metric Radar"
      data={data}
      algorithms={algorithms}
    />
  );
}
