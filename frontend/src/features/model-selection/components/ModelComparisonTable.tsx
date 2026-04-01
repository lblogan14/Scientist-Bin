import { Link } from "react-router";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { type Experiment, type ExperimentRecord, isExperimentError } from "@/types/api";

interface ModelComparisonTableProps {
  models: Experiment[];
}

export function ModelComparisonTable({ models }: ModelComparisonTableProps) {
  // Flatten experiment histories to show per-run comparison
  const allRecords: (ExperimentRecord & {
    experimentId: string;
    objective: string;
  })[] = [];
  for (const model of models) {
    const r = model.result;
    const history = r && !isExperimentError(r) ? r.experiment_history ?? [] : [];
    if (history.length > 0) {
      for (const record of history) {
        allRecords.push({
          ...record,
          experimentId: model.id,
          objective: model.objective,
        });
      }
    } else {
      // Fallback for experiments without history
      allRecords.push({
        iteration: 0,
        algorithm: model.framework ?? "unknown",
        hyperparameters: {},
        metrics: {},
        training_time_seconds: 0,
        timestamp: model.created_at,
        experimentId: model.id,
        objective: model.objective,
      });
    }
  }

  // Collect all metric names
  const allMetricNames = new Set<string>();
  for (const record of allRecords) {
    for (const key of Object.keys(record.metrics)) {
      allMetricNames.add(key);
    }
  }
  const metricNames = Array.from(allMetricNames).slice(0, 4); // limit to 4

  // Find best value per metric for highlighting
  const bestValues: Record<string, number> = {};
  for (const name of metricNames) {
    bestValues[name] = Math.max(
      ...allRecords.map((r) => r.metrics[name] ?? -Infinity),
    );
  }

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Objective</TableHead>
            <TableHead>Algorithm</TableHead>
            <TableHead>Iter</TableHead>
            {metricNames.map((name) => (
              <TableHead key={name}>{name}</TableHead>
            ))}
            <TableHead>Time (s)</TableHead>
            <TableHead></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {allRecords.map((record, i) => (
            <TableRow key={i}>
              <TableCell className="max-w-[200px] truncate">
                {record.objective}
              </TableCell>
              <TableCell>
                <Badge variant="outline">{record.algorithm}</Badge>
              </TableCell>
              <TableCell className="text-muted-foreground text-sm">
                {record.iteration}
              </TableCell>
              {metricNames.map((name) => {
                const val = record.metrics[name];
                const isBest = val != null && val === bestValues[name];
                return (
                  <TableCell
                    key={name}
                    className={`font-mono text-sm ${isBest ? "text-primary font-bold" : ""}`}
                  >
                    {val != null ? val.toFixed(4) : "-"}
                  </TableCell>
                );
              })}
              <TableCell className="text-muted-foreground text-sm">
                {record.training_time_seconds
                  ? record.training_time_seconds.toFixed(1)
                  : "-"}
              </TableCell>
              <TableCell>
                <Link
                  to={`/results?id=${record.experimentId}`}
                  className="text-primary text-sm hover:underline"
                >
                  Results
                </Link>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
