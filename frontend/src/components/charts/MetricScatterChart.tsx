import {
  CartesianGrid,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { ChartContainer } from "./ChartContainer";
import { useCssVars } from "@/hooks/use-css-vars";

interface MetricScatterChartProps {
  title: string;
  data: Array<{ name: string; x: number; y: number }>;
  xLabel: string;
  yLabel: string;
  height?: number;
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: { name: string; x: number; y: number } }>;
}) {
  if (!active || !payload?.length) return null;
  const d = payload[0]!.payload;
  return (
    <div className="bg-popover text-popover-foreground rounded-md border p-2 text-xs shadow-md">
      <p className="font-medium">{d.name}</p>
      <p>x: {d.x.toFixed(3)}</p>
      <p>y: {d.y.toFixed(4)}</p>
    </div>
  );
}

export function MetricScatterChart({
  title,
  data,
  xLabel,
  yLabel,
  height,
}: MetricScatterChartProps) {
  const [chartColor] = useCssVars(["--chart-1"]);

  if (!data || data.length === 0) return null;

  return (
    <ChartContainer title={title} height={height}>
      <ScatterChart>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="x"
          type="number"
          name={xLabel}
          label={{ value: xLabel, position: "insideBottom", offset: -5 }}
          tick={{ fontSize: 12 }}
        />
        <YAxis
          dataKey="y"
          type="number"
          name={yLabel}
          label={{ value: yLabel, angle: -90, position: "insideLeft" }}
          tick={{ fontSize: 12 }}
        />
        <ZAxis dataKey="name" type="category" />
        <Tooltip content={<CustomTooltip />} />
        <Scatter data={data} fill={chartColor} />
      </ScatterChart>
    </ChartContainer>
  );
}
