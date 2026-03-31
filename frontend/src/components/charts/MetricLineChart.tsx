import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts";
import { ChartContainer } from "./ChartContainer";

interface MetricLineChartProps {
  title: string;
  data: Record<string, unknown>[];
  xKey: string;
  yKey: string;
  color?: string;
}

export function MetricLineChart({
  title,
  data,
  xKey,
  yKey,
  color = "var(--chart-1)",
}: MetricLineChartProps) {
  return (
    <ChartContainer title={title}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={xKey} />
        <YAxis />
        <Line type="monotone" dataKey={yKey} stroke={color} strokeWidth={2} />
      </LineChart>
    </ChartContainer>
  );
}
