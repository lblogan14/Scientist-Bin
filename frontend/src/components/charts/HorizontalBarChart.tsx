import { Bar, BarChart, CartesianGrid, Tooltip, XAxis, YAxis } from "recharts";
import { ChartContainer } from "./ChartContainer";
import { useCssVars } from "@/hooks/use-css-vars";

interface HorizontalBarChartProps {
  title: string;
  data: Array<{ name: string; value: number }>;
  color?: string;
  height?: number;
}

export function HorizontalBarChart({
  title,
  data,
  color,
  height,
}: HorizontalBarChartProps) {
  const [resolvedDefault] = useCssVars(["--chart-2"]);
  const fillColor = color ?? resolvedDefault;

  if (!data || data.length === 0) return null;

  return (
    <ChartContainer title={title} height={height}>
      <BarChart data={data} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" />
        <YAxis
          dataKey="name"
          type="category"
          width={120}
          tick={{ fontSize: 12 }}
        />
        <Tooltip cursor={{ fill: "transparent" }} />
        <Bar dataKey="value" fill={fillColor} radius={[0, 4, 4, 0]} />
      </BarChart>
    </ChartContainer>
  );
}
