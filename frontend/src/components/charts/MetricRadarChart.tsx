import {
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  Tooltip,
} from "recharts";
import { ChartContainer } from "./ChartContainer";

const COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
];

interface MetricRadarChartProps {
  title: string;
  data: Array<{ metric: string; [algorithmName: string]: string | number }>;
  algorithms: string[];
  height?: number;
}

export function MetricRadarChart({
  title,
  data,
  algorithms,
  height,
}: MetricRadarChartProps) {
  if (!data || data.length === 0 || algorithms.length === 0) return null;

  return (
    <ChartContainer title={title} height={height}>
      <RadarChart data={data} cx="50%" cy="50%" outerRadius="70%">
        <PolarGrid />
        <PolarAngleAxis dataKey="metric" tick={{ fontSize: 12 }} />
        <PolarRadiusAxis domain={[0, 1]} tick={{ fontSize: 10 }} />
        <Tooltip />
        <Legend />
        {algorithms.map((algo, i) => (
          <Radar
            key={algo}
            name={algo}
            dataKey={algo}
            stroke={COLORS[i % COLORS.length]}
            fill={COLORS[i % COLORS.length]}
            fillOpacity={0.15}
          />
        ))}
      </RadarChart>
    </ChartContainer>
  );
}
