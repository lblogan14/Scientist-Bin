import { useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { HyperparamHeatmap } from "@/components/charts/HyperparamHeatmap";
import type {
  ChartData,
  ExperimentRecord,
  ExperimentResult,
} from "@/types/api";

interface HyperparameterTabProps {
  chartData?: ChartData;
  history?: ExperimentRecord[];
  result?: ExperimentResult;
}

export function HyperparameterTab({
  chartData,
  history,
  result,
}: HyperparameterTabProps) {
  // Build search data from chart_data or experiment history
  const searchData = chartData?.hyperparam_search;

  // Collect all algorithms with search results
  const algosFromChart = searchData ? Object.keys(searchData) : [];
  const algosFromHistory = (history ?? [])
    .filter((r) => r.cv_results_top_n?.length)
    .map((r) => r.algorithm);
  const allAlgos = Array.from(
    new Set([...algosFromChart, ...algosFromHistory]),
  );

  const [selectedAlgo, setSelectedAlgo] = useState(allAlgos[0] ?? "");

  if (allAlgos.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No hyperparameter search data available for this experiment.
      </p>
    );
  }

  const entries =
    searchData?.[selectedAlgo] ??
    history?.find((r) => r.algorithm === selectedAlgo)?.cv_results_top_n ??
    [];

  // Best hyperparameters from result
  const bestParams = result?.best_hyperparameters;

  return (
    <div className="space-y-6">
      {allAlgos.length > 1 && (
        <Select value={selectedAlgo} onValueChange={setSelectedAlgo}>
          <SelectTrigger className="w-64">
            <SelectValue placeholder="Select algorithm" />
          </SelectTrigger>
          <SelectContent>
            {allAlgos.map((algo) => (
              <SelectItem key={algo} value={algo}>
                {algo}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      {/* Best hyperparameters card */}
      {bestParams && Object.keys(bestParams).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Best Hyperparameters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {Object.entries(bestParams).map(([key, val]) => (
                <Badge
                  key={key}
                  variant="secondary"
                  className="font-mono text-xs"
                >
                  {key}={String(val)}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search results table */}
      <HyperparamHeatmap
        data={entries}
        title={`Hyperparameter Search — ${selectedAlgo}`}
      />
    </div>
  );
}
