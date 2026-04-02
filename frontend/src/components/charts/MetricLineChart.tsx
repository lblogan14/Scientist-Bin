import {
  CartesianGrid,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartContainer } from "./ChartContainer";
import { useCssVars } from "@/hooks/use-css-vars";

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
  color,
}: MetricLineChartProps) {
  const [resolvedDefault] = useCssVars(["--chart-1"]);
  const strokeColor = color ?? resolvedDefault;

  if (!data || data.length === 0) return null;

  return (
    <ChartContainer title={title}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={xKey} />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey={yKey} stroke={strokeColor} strokeWidth={2} />
      </LineChart>
    </ChartContainer>
  );
}
