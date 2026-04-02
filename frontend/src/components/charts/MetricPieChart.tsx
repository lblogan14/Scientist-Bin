import { Cell, Legend, Pie, PieChart, Tooltip } from "recharts";
import { ChartContainer } from "./ChartContainer";
import { useCssVars } from "@/hooks/use-css-vars";

interface MetricPieChartProps {
  title: string;
  data: Array<{ name: string; value: number }>;
  height?: number;
}

export function MetricPieChart({ title, data, height }: MetricPieChartProps) {
  const chartColors = useCssVars([
    "--chart-1",
    "--chart-2",
    "--chart-3",
    "--chart-4",
    "--chart-5",
  ]);

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
            <Cell key={i} fill={chartColors[i % chartColors.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ChartContainer>
  );
}
