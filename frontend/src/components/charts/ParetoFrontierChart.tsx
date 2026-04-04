import {
  CartesianGrid,
  ComposedChart,
  Line,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartContainer } from "./ChartContainer";
import { useCssVars } from "@/hooks/use-css-vars";

interface ParetoPoint {
  name: string;
  performance: number;
  time: number;
  isPareto?: boolean;
}

interface ParetoFrontierChartProps {
  data: ParetoPoint[];
  title?: string;
  xLabel?: string;
  yLabel?: string;
}

export function ParetoFrontierChart({
  data,
  title = "Performance vs Training Time",
  xLabel = "Training Time (s)",
  yLabel = "Performance",
}: ParetoFrontierChartProps) {
  const [c1, c3] = useCssVars(["--chart-1", "--chart-3"]);

  if (data.length === 0) return null;

  // Separate Pareto-optimal and non-Pareto points
  const paretoPoints = data
    .filter((d) => d.isPareto)
    .sort((a, b) => a.time - b.time);

  return (
    <ChartContainer title={title}>
      <ComposedChart
        data={paretoPoints}
        margin={{ left: 10, right: 20, bottom: 10 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="time"
          type="number"
          name={xLabel}
          tick={{ fontSize: 12 }}
          label={{
            value: xLabel,
            position: "insideBottom",
            offset: -5,
            fontSize: 11,
          }}
        />
        <YAxis
          dataKey="performance"
          type="number"
          name={yLabel}
          tick={{ fontSize: 12 }}
          label={{
            value: yLabel,
            angle: -90,
            position: "insideLeft",
            fontSize: 11,
          }}
          domain={["auto", "auto"]}
        />
        <Tooltip
          content={({ payload }) => {
            if (!payload?.[0]) return null;
            const d = payload[0].payload as ParetoPoint;
            const displayName =
              d.name.length > 30 ? d.name.slice(0, 27) + "..." : d.name;
            return (
              <div className="bg-background rounded-md border border-border p-2.5 text-xs shadow-lg">
                <div className="mb-1.5 flex items-center gap-1.5">
                  {d.isPareto && (
                    <span className="text-primary text-sm" title="Pareto-optimal">
                      ★
                    </span>
                  )}
                  <p className="font-semibold">{displayName}</p>
                </div>
                <p className="text-muted-foreground">
                  {yLabel}:{" "}
                  <span className="text-foreground font-mono">
                    {d.performance.toFixed(4)}
                  </span>
                </p>
                <p className="text-muted-foreground">
                  {xLabel}:{" "}
                  <span className="text-foreground font-mono">
                    {d.time.toFixed(1)}s
                  </span>
                </p>
                {d.isPareto && (
                  <p className="text-primary mt-1 text-[10px] font-medium uppercase tracking-wide">
                    Pareto-optimal
                  </p>
                )}
              </div>
            );
          }}
        />
        {/* All points */}
        <Scatter
          data={data.filter((d) => !d.isPareto)}
          fill={c3}
          fillOpacity={0.6}
        />
        {/* Pareto-optimal points */}
        <Scatter data={paretoPoints} fill={c1} shape="star" />
        {/* Pareto frontier line */}
        {paretoPoints.length > 1 && (
          <Line
            dataKey="performance"
            stroke={c1}
            strokeDasharray="5 3"
            dot={false}
            type="monotone"
          />
        )}
      </ComposedChart>
    </ChartContainer>
  );
}
