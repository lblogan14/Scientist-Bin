import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartContainer } from "./ChartContainer";
import type { FeatureImportance } from "@/types/api";

interface FeatureImportanceChartProps {
  features: FeatureImportance[];
  algorithm?: string;
  maxFeatures?: number;
}

export function FeatureImportanceChart({
  features,
  algorithm,
  maxFeatures = 15,
}: FeatureImportanceChartProps) {
  const data = features
    .slice(0, maxFeatures)
    .sort((a, b) => a.importance - b.importance)
    .map((f) => ({
      feature: f.feature,
      importance: Number(f.importance.toFixed(4)),
    }));

  const title = algorithm
    ? `Feature Importance — ${algorithm}`
    : "Feature Importance";

  return (
    <ChartContainer title={title}>
      <ResponsiveContainer
        width="100%"
        height={Math.max(data.length * 32, 200)}
      >
        <BarChart
          data={data}
          layout="vertical"
          margin={{ left: 20, right: 30 }}
        >
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 12 }} />
          <YAxis
            dataKey="feature"
            type="category"
            width={140}
            tick={{ fontSize: 11 }}
          />
          <Tooltip
            formatter={(value: number) => [value.toFixed(4), "Importance"]}
          />
          <Bar
            dataKey="importance"
            fill="hsl(var(--chart-1))"
            radius={[0, 4, 4, 0]}
            label={{
              position: "right",
              fontSize: 11,
              formatter: (val: number) => val.toFixed(3),
            }}
          />
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
}
