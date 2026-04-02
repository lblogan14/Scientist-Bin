import { useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { MetricBarChart } from "@/components/charts/MetricBarChart";
import type { ClusterStats, ExperimentRecord, ChartData } from "@/types/api";

interface ClusterAnalysisTabProps {
  /** chart_data from summary agent */
  chartData?: ChartData;
  /** Fallback: per-record cluster stats */
  history?: ExperimentRecord[];
}

function getClusterStats(
  props: ClusterAnalysisTabProps,
): Record<string, ClusterStats> {
  const fromChart = props.chartData?.cluster_stats;
  if (fromChart && Object.keys(fromChart).length > 0) {
    return fromChart;
  }
  const out: Record<string, ClusterStats> = {};
  for (const rec of props.history ?? []) {
    if (rec.cluster_stats) {
      out[rec.algorithm] = rec.cluster_stats;
    }
  }
  return out;
}

function formatMetric(value: number): string {
  return Number.isFinite(value) ? value.toFixed(4) : String(value);
}

export function ClusterAnalysisTab(props: ClusterAnalysisTabProps) {
  const allStats = getClusterStats(props);
  const algorithms = Object.keys(allStats);
  const [selected, setSelected] = useState(algorithms[0] ?? "");

  if (algorithms.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No cluster analysis data available for this experiment.
      </p>
    );
  }

  const stats = allStats[selected];

  // Build cluster size chart data
  const clusterSizeData = stats?.cluster_sizes
    ? stats.cluster_sizes.map((size, i) => ({
        cluster: `Cluster ${i}`,
        size,
      }))
    : [];

  return (
    <div className="space-y-4">
      {algorithms.length > 1 && (
        <Select value={selected} onValueChange={setSelected}>
          <SelectTrigger className="w-64">
            <SelectValue placeholder="Select algorithm" />
          </SelectTrigger>
          <SelectContent>
            {algorithms.map((algo) => (
              <SelectItem key={algo} value={algo}>
                {algo}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      {stats && (
        <>
          {/* Key clustering metrics */}
          <div className="grid gap-4 sm:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-muted-foreground text-xs font-medium uppercase">
                  Silhouette Score
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {formatMetric(stats.silhouette_score)}
                </p>
                <p className="text-muted-foreground text-xs">
                  Range: -1 to 1 (higher is better)
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-muted-foreground text-xs font-medium uppercase">
                  Calinski-Harabasz
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {formatMetric(stats.calinski_harabasz_score)}
                </p>
                <p className="text-muted-foreground text-xs">
                  Higher is better
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-muted-foreground text-xs font-medium uppercase">
                  Davies-Bouldin
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {formatMetric(stats.davies_bouldin_score)}
                </p>
                <p className="text-muted-foreground text-xs">
                  Lower is better
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {/* Cluster sizes */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">
                  Cluster Summary — {selected}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Statistic</TableHead>
                      <TableHead className="text-right">Value</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow>
                      <TableCell className="font-medium">
                        Number of Clusters
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {stats.n_clusters}
                      </TableCell>
                    </TableRow>
                    {stats.cluster_sizes.map((size, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-medium">
                          Cluster {i} Size
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {size}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            {/* Cluster size bar chart */}
            {clusterSizeData.length > 0 && (
              <MetricBarChart
                title={`Cluster Sizes — ${selected}`}
                data={clusterSizeData}
                xKey="cluster"
                yKey="size"
              />
            )}
          </div>
        </>
      )}

      {/* Comparison table when multiple algorithms */}
      {algorithms.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Clustering Comparison
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Algorithm</TableHead>
                  <TableHead className="text-right">Clusters</TableHead>
                  <TableHead className="text-right">Silhouette</TableHead>
                  <TableHead className="text-right">Calinski-Harabasz</TableHead>
                  <TableHead className="text-right">Davies-Bouldin</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {algorithms.map((algo) => {
                  const s = allStats[algo];
                  if (!s) return null;
                  return (
                    <TableRow key={algo}>
                      <TableCell className="font-medium">{algo}</TableCell>
                      <TableCell className="text-right font-mono">
                        {s.n_clusters}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {formatMetric(s.silhouette_score)}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {formatMetric(s.calinski_harabasz_score)}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {formatMetric(s.davies_bouldin_score)}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
