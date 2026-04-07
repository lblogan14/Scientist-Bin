import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from "recharts";
import { ChartContainer } from "@/components/charts/ChartContainer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TabContext } from "../tab-registry";
import type { ActualVsPredictedPoint } from "@/types/api";

export function ActualVsPredictedTab({
  chartData,
  experimentHistory,
}: TabContext) {
  const data: ActualVsPredictedPoint[] =
    chartData?.actual_vs_predicted ??
    experimentHistory.findLast((r) => r.actual_vs_predicted?.length)
      ?.actual_vs_predicted ??
    [];

  if (data.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No actual vs predicted data available.
      </p>
    );
  }

  // Compute axis range for the perfect prediction line
  const allValues = data.flatMap((d) => [d.actual, d.predicted]);
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);

  // Compute R2 and RMSE from the data
  const meanActual = data.reduce((s, d) => s + d.actual, 0) / data.length;
  const ssTot = data.reduce((s, d) => s + (d.actual - meanActual) ** 2, 0);
  const ssRes = data.reduce(
    (s, d) => s + (d.actual - d.predicted) ** 2,
    0,
  );
  const r2 = ssTot > 0 ? 1 - ssRes / ssTot : 0;
  const rmse = Math.sqrt(ssRes / data.length);

  return (
    <div className="space-y-4">
      {/* Metric summary */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">R2 Score</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-2xl font-bold">{r2.toFixed(4)}</span>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">RMSE</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-2xl font-bold">{rmse.toFixed(4)}</span>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Samples</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-2xl font-bold">{data.length}</span>
          </CardContent>
        </Card>
      </div>

      {/* Scatter plot */}
      <ChartContainer title="Actual vs Predicted" height={400}>
        <ScatterChart margin={{ top: 10, right: 30, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            type="number"
            dataKey="actual"
            name="Actual"
            domain={[min, max]}
            label={{ value: "Actual", position: "insideBottom", offset: -10 }}
          />
          <YAxis
            type="number"
            dataKey="predicted"
            name="Predicted"
            domain={[min, max]}
            label={{
              value: "Predicted",
              angle: -90,
              position: "insideLeft",
            }}
          />
          <Tooltip
            content={({ payload }) => {
              if (!payload?.[0]) return null;
              const p = payload[0].payload as ActualVsPredictedPoint;
              return (
                <div className="bg-background border rounded p-2 text-xs shadow">
                  <p>Actual: {p.actual.toFixed(4)}</p>
                  <p>Predicted: {p.predicted.toFixed(4)}</p>
                  <p>Error: {(p.actual - p.predicted).toFixed(4)}</p>
                </div>
              );
            }}
          />
          {/* Perfect prediction diagonal */}
          <ReferenceLine
            segment={[
              { x: min, y: min },
              { x: max, y: max },
            ]}
            stroke="var(--chart-3)"
            strokeDasharray="5 5"
            label={{ value: "Perfect", position: "insideTopLeft" }}
          />
          <Scatter
            data={data}
            fill="var(--chart-1)"
            opacity={0.6}
            r={3}
          />
        </ScatterChart>
      </ChartContainer>
    </div>
  );
}
