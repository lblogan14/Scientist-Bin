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
import { useCssVars } from "@/hooks/use-css-vars";

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
  const chartColors = useCssVars([
    "--chart-1",
    "--chart-2",
    "--chart-3",
    "--chart-4",
    "--chart-5",
  ]);

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
            stroke={chartColors[i % chartColors.length]}
            fill={chartColors[i % chartColors.length]}
            fillOpacity={0.15}
          />
        ))}
      </RadarChart>
    </ChartContainer>
  );
}
