import { Bar, BarChart, CartesianGrid, Tooltip, XAxis, YAxis } from "recharts";
import { ChartContainer } from "./ChartContainer";

interface MetricBarChartProps {
  title: string;
  data: Record<string, unknown>[];
  xKey: string;
  yKey: string;
  color?: string;
}

export function MetricBarChart({
  title,
  data,
  xKey,
  yKey,
  color = "var(--chart-1)",
}: MetricBarChartProps) {
  return (
    <ChartContainer title={title}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={xKey} />
        <YAxis />
        <Tooltip cursor={{ fill: "var(--color-muted)" }} />
        <Bar dataKey={yKey} fill={color} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ChartContainer>
  );
}
