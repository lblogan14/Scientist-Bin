import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { ChartContainer } from "@/components/charts/ChartContainer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { TabContext } from "../tab-registry";
import type { ClusterScatterPoint } from "@/types/api";

const CLUSTER_COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
  "#8884d8",
  "#82ca9d",
  "#ffc658",
  "#ff7300",
  "#0088fe",
];

export function ClusterScatterTab({
  chartData,
  experimentHistory,
}: TabContext) {
  // Get scatter data from chart_data or latest experiment record
  const scatterData: ClusterScatterPoint[] =
    chartData?.cluster_scatter ??
    experimentHistory.findLast((r) => r.cluster_scatter?.length)
      ?.cluster_scatter ??
    [];

  if (scatterData.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No cluster visualization data available.
      </p>
    );
  }

  // Group points by cluster
  const clusters = new Map<number, ClusterScatterPoint[]>();
  for (const pt of scatterData) {
    const list = clusters.get(pt.cluster) ?? [];
    list.push(pt);
    clusters.set(pt.cluster, list);
  }

  const clusterIds = [...clusters.keys()].sort((a, b) => a - b);

  // Get cluster sizes from experiment history
  const clusterSizes =
    experimentHistory.findLast((r) => r.cluster_sizes)?.cluster_sizes ?? [];

  return (
    <div className="space-y-4">
      {/* Cluster size summary */}
      {clusterSizes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Cluster Sizes
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {clusterSizes.map((size, i) => (
              <Badge key={i} variant="outline">
                Cluster {i}: {size} samples
              </Badge>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Scatter plot */}
      <ChartContainer title="Cluster Scatter (PCA 2D Projection)" height={400}>
        <ScatterChart margin={{ top: 10, right: 30, bottom: 10, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" dataKey="x" name="PC1" />
          <YAxis type="number" dataKey="y" name="PC2" />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            content={({ payload }) => {
              if (!payload?.[0]) return null;
              const p = payload[0].payload as ClusterScatterPoint;
              return (
                <div className="bg-background border rounded p-2 text-xs shadow">
                  <p>Cluster: {p.cluster}</p>
                  <p>PC1: {p.x.toFixed(3)}</p>
                  <p>PC2: {p.y.toFixed(3)}</p>
                </div>
              );
            }}
          />
          <Legend />
          {clusterIds.map((id) => (
            <Scatter
              key={id}
              name={`Cluster ${id}`}
              data={clusters.get(id)}
              fill={CLUSTER_COLORS[id % CLUSTER_COLORS.length]}
              opacity={0.7}
              r={3}
            />
          ))}
        </ScatterChart>
      </ChartContainer>
    </div>
  );
}
