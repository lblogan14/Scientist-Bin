import { useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { BoxPlotChart } from "@/components/charts/BoxPlotChart";
import type { ChartData, ExperimentRecord } from "@/types/api";

interface CVStabilityTabProps {
  chartData?: ChartData;
  history?: ExperimentRecord[];
}

function getRiskBadge(cv: number) {
  if (cv < 0.05)
    return (
      <Badge className="bg-success/15 text-success">Stable</Badge>
    );
  if (cv < 0.1)
    return (
      <Badge className="bg-warning/15 text-warning">Moderate</Badge>
    );
  return (
    <Badge className="bg-destructive/15 text-destructive">Unstable</Badge>
  );
}

export function CVStabilityTab({ chartData, history }: CVStabilityTabProps) {
  // Build fold data from chart_data or experiment history
  const cvData = chartData?.cv_fold_scores;

  // Collect all available metrics across algorithms
  const metricsSet = new Set<string>();
  if (cvData) {
    for (const algo of Object.values(cvData)) {
      for (const metric of Object.keys(algo)) {
        metricsSet.add(metric);
      }
    }
  } else {
    for (const rec of history ?? []) {
      if (rec.cv_fold_scores) {
        for (const metric of Object.keys(rec.cv_fold_scores)) {
          metricsSet.add(metric);
        }
      }
    }
  }

  const metrics = Array.from(metricsSet);
  const [selectedMetric, setSelectedMetric] = useState(metrics[0] ?? "");

  if (metrics.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No cross-validation fold data available for this experiment.
      </p>
    );
  }

  // Build box plot data for the selected metric
  const boxData: { name: string; scores: number[]; mean: number }[] = [];
  const tableData: {
    algorithm: string;
    mean: number;
    std: number;
    cv: number;
    min: number;
    max: number;
    folds: number;
  }[] = [];

  if (cvData) {
    for (const [algo, metricMap] of Object.entries(cvData)) {
      const entry = metricMap[selectedMetric];
      if (!entry) continue;
      boxData.push({ name: algo, scores: entry.scores, mean: entry.mean });
      const std = Math.sqrt(
        entry.scores.reduce((sum, s) => sum + (s - entry.mean) ** 2, 0) /
          entry.scores.length,
      );
      tableData.push({
        algorithm: algo,
        mean: entry.mean,
        std,
        cv: entry.mean > 0 ? std / entry.mean : 0,
        min: Math.min(...entry.scores),
        max: Math.max(...entry.scores),
        folds: entry.scores.length,
      });
    }
  } else {
    for (const rec of history ?? []) {
      const scores = rec.cv_fold_scores?.[selectedMetric];
      if (!scores) continue;
      const mean = scores.reduce((a, b) => a + b, 0) / scores.length;
      boxData.push({ name: rec.algorithm, scores, mean });
      const std = Math.sqrt(
        scores.reduce((sum, s) => sum + (s - mean) ** 2, 0) / scores.length,
      );
      tableData.push({
        algorithm: rec.algorithm,
        mean,
        std,
        cv: mean > 0 ? std / mean : 0,
        min: Math.min(...scores),
        max: Math.max(...scores),
        folds: scores.length,
      });
    }
  }

  return (
    <div className="space-y-6">
      {metrics.length > 1 && (
        <Select value={selectedMetric} onValueChange={setSelectedMetric}>
          <SelectTrigger className="w-64">
            <SelectValue placeholder="Select metric" />
          </SelectTrigger>
          <SelectContent>
            {metrics.map((m) => (
              <SelectItem key={m} value={m}>
                {m}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      <BoxPlotChart
        data={boxData}
        title={`CV Fold Distribution — ${selectedMetric}`}
      />

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Algorithm</TableHead>
            <TableHead className="text-right">Mean</TableHead>
            <TableHead className="text-right">Std</TableHead>
            <TableHead className="text-right">Min</TableHead>
            <TableHead className="text-right">Max</TableHead>
            <TableHead className="text-right">Folds</TableHead>
            <TableHead>Stability</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {tableData.map((row) => (
            <TableRow key={row.algorithm}>
              <TableCell className="font-medium">
                <span className="block max-w-[180px] truncate">{row.algorithm}</span>
              </TableCell>
              <TableCell className="text-right font-mono">
                {row.mean.toFixed(4)}
              </TableCell>
              <TableCell className="text-right font-mono">
                {row.std.toFixed(4)}
              </TableCell>
              <TableCell className="text-right font-mono">
                {row.min.toFixed(4)}
              </TableCell>
              <TableCell className="text-right font-mono">
                {row.max.toFixed(4)}
              </TableCell>
              <TableCell className="text-right">{row.folds}</TableCell>
              <TableCell>{getRiskBadge(row.cv)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
