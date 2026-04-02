import {
  Bar,
  CartesianGrid,
  ComposedChart,
  ErrorBar,
  ResponsiveContainer,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartContainer } from "./ChartContainer";

interface BoxPlotData {
  name: string;
  scores: number[];
  mean: number;
}

interface BoxPlotChartProps {
  data: BoxPlotData[];
  title?: string;
}

function computeStats(scores: number[]) {
  const sorted = [...scores].sort((a, b) => a - b);
  const n = sorted.length;
  const q1 = sorted[Math.floor(n * 0.25)] ?? 0;
  const median = sorted[Math.floor(n * 0.5)] ?? 0;
  const q3 = sorted[Math.floor(n * 0.75)] ?? 0;
  const min = sorted[0] ?? 0;
  const max = sorted[n - 1] ?? 0;
  const iqr = q3 - q1;
  return { min, q1, median, q3, max, iqr };
}

export function BoxPlotChart({
  data,
  title = "CV Fold Distribution",
}: BoxPlotChartProps) {
  // Build bar data (IQR range) with error bars for whiskers
  const chartData = data.map((d) => {
    const stats = computeStats(d.scores);
    return {
      name: d.name,
      // The bar represents the IQR (q1 to q3)
      base: stats.q1,
      iqr: stats.q3 - stats.q1,
      median: stats.median,
      mean: d.mean,
      min: stats.min,
      max: stats.max,
      // Error bar goes from q1-min (lower) to max-q3 (upper)
      whiskerLower: stats.q1 - stats.min,
      whiskerUpper: stats.max - stats.q3,
    };
  });

  // Scatter points for individual folds
  const scatterData = data.flatMap((d) =>
    d.scores.map((score) => ({
      name: d.name,
      score,
    })),
  );

  return (
    <ChartContainer title={title}>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={chartData} margin={{ left: 10, right: 20 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 12 }} domain={["auto", "auto"]} />
          <Tooltip
            formatter={(value: number, name: string) => [
              value.toFixed(4),
              name,
            ]}
          />
          {/* IQR bar starting from base (q1) */}
          <Bar
            dataKey="iqr"
            fill="hsl(var(--chart-2))"
            fillOpacity={0.6}
            stroke="hsl(var(--chart-2))"
            stackId="box"
            barSize={30}
          >
            <ErrorBar
              dataKey="whiskerUpper"
              width={10}
              strokeWidth={1.5}
              direction="y"
            />
          </Bar>
          {/* Individual fold scores */}
          <Scatter
            data={scatterData}
            dataKey="score"
            fill="hsl(var(--chart-1))"
            r={3}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
}
