import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from "recharts";
import { ChartContainer } from "@/components/charts/ChartContainer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { TabContext } from "../tab-registry";
import type { ElbowPoint } from "@/types/api";

export function ElbowCurveTab({ chartData, experimentHistory }: TabContext) {
  const elbowData: ElbowPoint[] =
    chartData?.elbow_curve ??
    experimentHistory.findLast((r) => r.elbow_data?.length)?.elbow_data ??
    [];

  if (elbowData.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No elbow curve data available.
      </p>
    );
  }

  // Determine the chosen k from the best experiment
  const chosenK =
    experimentHistory.findLast((r) => r.n_clusters)?.n_clusters ?? null;

  return (
    <div className="space-y-4">
      {chosenK && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Selected Number of Clusters
            </CardTitle>
          </CardHeader>
          <CardContent className="flex items-center gap-2">
            <Badge variant="default" className="text-lg">
              k = {chosenK}
            </Badge>
            <span className="text-muted-foreground text-sm">
              Selected based on elbow analysis and clustering metrics
            </span>
          </CardContent>
        </Card>
      )}

      <ChartContainer title="Elbow Curve (Inertia vs Number of Clusters)" height={350}>
        <LineChart data={elbowData} margin={{ top: 10, right: 30, bottom: 10, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="k"
            label={{ value: "Number of Clusters (k)", position: "insideBottom", offset: -5 }}
          />
          <YAxis
            label={{ value: "Inertia", angle: -90, position: "insideLeft" }}
          />
          <Tooltip
            content={({ payload }) => {
              if (!payload?.[0]) return null;
              const p = payload[0].payload as ElbowPoint;
              return (
                <div className="bg-background border rounded p-2 text-xs shadow">
                  <p>k = {p.k}</p>
                  <p>Inertia: {p.inertia.toFixed(2)}</p>
                </div>
              );
            }}
          />
          {chosenK && (
            <ReferenceLine
              x={chosenK}
              stroke="var(--chart-3)"
              strokeDasharray="5 5"
              label={{ value: `k=${chosenK}`, position: "top" }}
            />
          )}
          <Line
            type="monotone"
            dataKey="inertia"
            stroke="var(--chart-1)"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ChartContainer>
    </div>
  );
}
