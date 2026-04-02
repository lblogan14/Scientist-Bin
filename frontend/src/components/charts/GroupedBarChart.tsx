import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartContainer } from "./ChartContainer";
import { useCssVars } from "@/hooks/use-css-vars";

interface GroupedBarChartProps {
  title: string;
  data: Record<string, unknown>[];
  xKey: string;
  yKeys: string[];
  colors?: string[];
  height?: number;
}

export function GroupedBarChart({
  title,
  data,
  xKey,
  yKeys,
  colors,
  height,
}: GroupedBarChartProps) {
  const resolvedColors = useCssVars([
    "--chart-1",
    "--chart-2",
    "--chart-3",
    "--chart-4",
    "--chart-5",
  ]);
  const fillColors = colors ?? resolvedColors;

  if (!data || data.length === 0) return null;

  return (
    <ChartContainer title={title} height={height}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
        <YAxis />
        <Tooltip cursor={{ fill: "transparent" }} />
        <Legend />
        {yKeys.map((key, i) => (
          <Bar
            key={key}
            dataKey={key}
            fill={fillColors[i % fillColors.length]}
            radius={[4, 4, 0, 0]}
          />
        ))}
      </BarChart>
    </ChartContainer>
  );
}
