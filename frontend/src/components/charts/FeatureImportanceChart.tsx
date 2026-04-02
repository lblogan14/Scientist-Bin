import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartContainer } from "./ChartContainer";
import { useCssVars } from "@/hooks/use-css-vars";
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
  const [c1, c2] = useCssVars(["--chart-1", "--chart-2"]);

  const sorted = features
    .slice(0, maxFeatures)
    .sort((a, b) => a.importance - b.importance);

  const maxVal = sorted[sorted.length - 1]?.importance ?? 1;

  const data = sorted.map((f) => ({
    feature: f.feature,
    importance: Number(f.importance.toFixed(4)),
    ratio: maxVal > 0 ? f.importance / maxVal : 0,
  }));

  const title = algorithm
    ? `Feature Importance — ${algorithm}`
    : "Feature Importance";

  return (
    <ChartContainer title={title} height={Math.max(data.length * 32, 200)}>
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
          radius={[0, 4, 4, 0]}
          label={{
            position: "right",
            fontSize: 11,
            formatter: (val: number) => val.toFixed(3),
          }}
        >
          {data.map((entry, index) => {
            // Blend chart-1 (high) → chart-2 (low) by importance ratio
            const opacity = 0.3 + entry.ratio * 0.7;
            const fill = entry.ratio > 0.5 ? c1 : c2;
            return <Cell key={index} fill={fill} fillOpacity={opacity} />;
          })}
        </Bar>
      </BarChart>
    </ChartContainer>
  );
}
