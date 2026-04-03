import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Legend,
  Tooltip,
} from "recharts";
import { ChartContainer } from "@/components/charts/ChartContainer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { TabContext } from "../tab-registry";
import type { ClusterProfile } from "@/types/api";

const CLUSTER_COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
  "#8884d8",
  "#82ca9d",
  "#ffc658",
];

export function ClusterProfileTab({
  chartData,
  experimentHistory,
}: TabContext) {
  const profiles: ClusterProfile[] =
    chartData?.cluster_profiles ??
    experimentHistory.findLast((r) => r.cluster_profiles?.length)
      ?.cluster_profiles ??
    [];

  if (profiles.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No cluster profile data available.
      </p>
    );
  }

  // Build radar chart data: one entry per feature, with a value for each cluster
  const allFeatures = Object.keys(profiles[0]?.centroid ?? {});
  // Limit to top 8 features for radar readability
  const features = allFeatures.slice(0, 8);

  // Normalize feature values across clusters for radar comparability
  const featureRanges = features.map((f) => {
    const values = profiles.map((p) => p.centroid[f] ?? 0);
    const min = Math.min(...values);
    const max = Math.max(...values);
    return { feature: f, min, max, range: max - min || 1 };
  });

  const radarData = featureRanges.map(({ feature, min, range }) => {
    const entry: Record<string, string | number> = { feature };
    for (const p of profiles) {
      entry[`cluster_${p.cluster_id}`] = Number(
        (((p.centroid[feature] ?? 0) - min) / range).toFixed(3),
      );
    }
    return entry;
  });

  return (
    <div className="space-y-4">
      {/* Radar chart */}
      {features.length >= 3 && (
        <ChartContainer
          title="Cluster Profile Comparison (Normalized)"
          height={400}
        >
          <RadarChart data={radarData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="feature" tick={{ fontSize: 11 }} />
            <PolarRadiusAxis domain={[0, 1]} tick={false} />
            <Tooltip />
            <Legend />
            {profiles.map((p, i) => (
              <Radar
                key={p.cluster_id}
                name={`Cluster ${p.cluster_id}`}
                dataKey={`cluster_${p.cluster_id}`}
                stroke={CLUSTER_COLORS[i % CLUSTER_COLORS.length]}
                fill={CLUSTER_COLORS[i % CLUSTER_COLORS.length]}
                fillOpacity={0.15}
              />
            ))}
          </RadarChart>
        </ChartContainer>
      )}

      {/* Cluster details table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">
            Cluster Centroids
          </CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Cluster</TableHead>
                <TableHead>Size</TableHead>
                {features.map((f) => (
                  <TableHead key={f}>{f}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {profiles.map((p) => (
                <TableRow key={p.cluster_id}>
                  <TableCell>
                    <Badge variant="outline">Cluster {p.cluster_id}</Badge>
                  </TableCell>
                  <TableCell>{p.size}</TableCell>
                  {features.map((f) => (
                    <TableCell key={f}>
                      {(p.centroid[f] ?? 0).toFixed(3)}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
