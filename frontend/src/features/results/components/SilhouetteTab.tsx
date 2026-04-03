import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Cell,
} from "recharts";
import { ChartContainer } from "@/components/charts/ChartContainer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { TabContext } from "../tab-registry";
import type { SilhouetteSample } from "@/types/api";

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

export function SilhouetteTab({ chartData, experimentHistory }: TabContext) {
  const silhouetteData: SilhouetteSample[] =
    chartData?.silhouette_data ??
    experimentHistory.findLast((r) => r.silhouette_per_sample?.length)
      ?.silhouette_per_sample ??
    [];

  if (silhouetteData.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No silhouette data available.
      </p>
    );
  }

  // Compute average silhouette score
  const avgScore =
    silhouetteData.reduce((sum, d) => sum + d.score, 0) / silhouetteData.length;

  // Sort by cluster then by score within cluster (for the classic silhouette plot shape)
  const sorted = [...silhouetteData].sort((a, b) => {
    if (a.cluster !== b.cluster) return a.cluster - b.cluster;
    return b.score - a.score;
  });

  // Prepare bar chart data (limit to 500 bars for SVG performance)
  const step = Math.max(1, Math.floor(sorted.length / 500));
  const barData = sorted
    .filter((_, i) => i % step === 0)
    .map((d, i) => ({ index: i, ...d }));

  // Score quality badge
  const quality =
    avgScore >= 0.5 ? "Strong" : avgScore >= 0.25 ? "Moderate" : "Weak";
  const qualityVariant =
    avgScore >= 0.5
      ? ("default" as const)
      : avgScore >= 0.25
        ? ("secondary" as const)
        : ("destructive" as const);

  return (
    <div className="space-y-4">
      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Average Silhouette Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">{avgScore.toFixed(3)}</span>
              <Badge variant={qualityVariant}>{quality}</Badge>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Samples</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-2xl font-bold">{silhouetteData.length}</span>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Clusters</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-2xl font-bold">
              {new Set(silhouetteData.map((d) => d.cluster)).size}
            </span>
          </CardContent>
        </Card>
      </div>

      {/* Silhouette bar chart */}
      <ChartContainer title="Silhouette Coefficients by Sample" height={400}>
        <BarChart
          data={barData}
          layout="vertical"
          margin={{ top: 10, right: 30, bottom: 10, left: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" domain={[-0.2, 1]} />
          <YAxis type="category" dataKey="index" hide />
          <Tooltip
            content={({ payload }) => {
              if (!payload?.[0]) return null;
              const p = payload[0].payload as SilhouetteSample & {
                index: number;
              };
              return (
                <div className="bg-background border rounded p-2 text-xs shadow">
                  <p>Cluster: {p.cluster}</p>
                  <p>Score: {p.score.toFixed(3)}</p>
                </div>
              );
            }}
          />
          <ReferenceLine
            x={avgScore}
            stroke="red"
            strokeDasharray="5 5"
            label={{ value: `avg=${avgScore.toFixed(3)}`, position: "top" }}
          />
          <Bar dataKey="score" maxBarSize={3}>
            {barData.map((d, i) => (
              <Cell
                key={i}
                fill={CLUSTER_COLORS[d.cluster % CLUSTER_COLORS.length]}
              />
            ))}
          </Bar>
        </BarChart>
      </ChartContainer>
    </div>
  );
}
