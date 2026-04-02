import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartContainer } from "./ChartContainer";
import type { OverfitEntry } from "@/types/api";

interface OverfitGaugeChartProps {
  entries: OverfitEntry[];
  title?: string;
}

export function OverfitGaugeChart({
  entries,
  title = "Overfitting Analysis",
}: OverfitGaugeChartProps) {
  const data = entries.map((e) => ({
    name: `${e.algorithm}\n(${e.metric_name})`,
    Train: Number(e.train_value.toFixed(4)),
    Validation: Number(e.val_value.toFixed(4)),
    gap: Number(e.gap_percentage.toFixed(1)),
    risk: e.overfit_risk,
  }));

  return (
    <ChartContainer title={title}>
      <ResponsiveContainer
        width="100%"
        height={Math.max(data.length * 50, 200)}
      >
        <BarChart
          data={data}
          layout="vertical"
          margin={{ left: 20, right: 40 }}
        >
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 12 }} domain={[0, "auto"]} />
          <YAxis
            dataKey="name"
            type="category"
            width={150}
            tick={{ fontSize: 11 }}
          />
          <Tooltip
            formatter={(value: number, name: string) => [
              value.toFixed(4),
              name,
            ]}
          />
          <Legend />
          <Bar
            dataKey="Train"
            fill="hsl(var(--chart-1))"
            radius={[0, 4, 4, 0]}
            barSize={16}
          />
          <Bar
            dataKey="Validation"
            fill="hsl(var(--chart-2))"
            radius={[0, 4, 4, 0]}
            barSize={16}
          />
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
}
