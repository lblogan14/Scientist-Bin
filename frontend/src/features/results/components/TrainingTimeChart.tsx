import { HorizontalBarChart } from "@/components/charts/HorizontalBarChart";
import type { ExperimentRecord } from "@/types/api";

interface TrainingTimeChartProps {
  history: ExperimentRecord[];
}

export function TrainingTimeChart({ history }: TrainingTimeChartProps) {
  if (history.length === 0) return null;

  const chartData = history.map((r) => ({
    name: r.algorithm,
    value: Math.round(r.training_time_seconds * 100) / 100,
  }));

  return (
    <HorizontalBarChart title="Training Time (seconds)" data={chartData} />
  );
}
