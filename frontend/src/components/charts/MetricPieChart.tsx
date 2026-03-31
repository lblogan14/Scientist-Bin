import { Cell, Legend, Pie, PieChart, Tooltip } from "recharts";
import { ChartContainer } from "./ChartContainer";

const COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
];

interface MetricPieChartProps {
  title: string;
  data: Array<{ name: string; value: number }>;
  height?: number;
}

export function MetricPieChart({ title, data, height }: MetricPieChartProps) {
  if (!data || data.length === 0) return null;

  return (
    <ChartContainer title={title} height={height}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="50%"
          innerRadius="40%"
          outerRadius="70%"
          paddingAngle={2}
          label={({ name, percent }) =>
            `${name} (${(percent * 100).toFixed(0)}%)`
          }
          labelLine={false}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ChartContainer>
  );
}
