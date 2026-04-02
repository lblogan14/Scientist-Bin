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
import type { ResidualStats, ExperimentRecord } from "@/types/api";

interface ResidualAnalysisTabProps {
  /** chart_data.residual_stats from summary agent */
  residualStats?: Record<string, ResidualStats>;
  /** Fallback: per-record residual stats */
  history?: ExperimentRecord[];
}

function getResiduals(
  props: ResidualAnalysisTabProps,
): Record<string, ResidualStats> {
  if (props.residualStats && Object.keys(props.residualStats).length > 0) {
    return props.residualStats;
  }
  const out: Record<string, ResidualStats> = {};
  for (const rec of props.history ?? []) {
    if (rec.residual_stats) {
      out[rec.algorithm] = rec.residual_stats;
    }
  }
  return out;
}

export function ResidualAnalysisTab(props: ResidualAnalysisTabProps) {
  const residuals = getResiduals(props);
  const algorithms = Object.keys(residuals);
  const [selected, setSelected] = useState(algorithms[0] ?? "");

  if (algorithms.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No residual analysis data available for this experiment.
      </p>
    );
  }

  const stats = residuals[selected];

  // Build percentile chart data
  const percentileData = stats?.residual_percentiles
    ? Object.entries(stats.residual_percentiles).map(([pct, value]) => ({
        percentile: `P${pct}`,
        value: Number(value),
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
        <div className="grid gap-4 md:grid-cols-2">
          {/* Residual statistics table */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">
                Residual Statistics — {selected}
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
                    <TableCell className="font-medium">Mean Residual</TableCell>
                    <TableCell className="text-right font-mono">
                      {stats.mean_residual.toFixed(4)}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">Std Residual</TableCell>
                    <TableCell className="text-right font-mono">
                      {stats.std_residual.toFixed(4)}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">
                      Max |Residual|
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {stats.max_abs_residual.toFixed(4)}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Residual percentile chart */}
          {percentileData.length > 0 && (
            <MetricBarChart
              title={`Residual Percentiles — ${selected}`}
              data={percentileData}
              xKey="percentile"
              yKey="value"
            />
          )}
        </div>
      )}

      {/* Comparison table when multiple algorithms */}
      {algorithms.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Residual Comparison
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Algorithm</TableHead>
                  <TableHead className="text-right">Mean Residual</TableHead>
                  <TableHead className="text-right">Std Residual</TableHead>
                  <TableHead className="text-right">Max |Residual|</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {algorithms.map((algo) => {
                  const s = residuals[algo];
                  if (!s) return null;
                  return (
                    <TableRow key={algo}>
                      <TableCell className="font-medium">{algo}</TableCell>
                      <TableCell className="text-right font-mono">
                        {s.mean_residual.toFixed(4)}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {s.std_residual.toFixed(4)}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {s.max_abs_residual.toFixed(4)}
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
