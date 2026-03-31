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
import type { ExperimentRecord } from "@/types/api";

interface EvaluationReportProps {
  evaluation: Record<string, unknown> | null;
  experimentHistory?: ExperimentRecord[];
}

export function EvaluationReport({
  evaluation,
  experimentHistory,
}: EvaluationReportProps) {
  const hasHistory = experimentHistory && experimentHistory.length > 0;

  if (!evaluation && !hasHistory) return null;

  // Collect all unique metric names across experiments
  const allMetricNames = new Set<string>();
  if (hasHistory) {
    for (const record of experimentHistory) {
      for (const key of Object.keys(record.metrics)) {
        allMetricNames.add(key);
      }
    }
  }
  const metricNames = Array.from(allMetricNames);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Experiment History
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {hasHistory ? (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Iter</TableHead>
                  <TableHead>Algorithm</TableHead>
                  {metricNames.map((name) => (
                    <TableHead key={name}>{name}</TableHead>
                  ))}
                  <TableHead>Time (s)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {experimentHistory.map((record, i) => {
                  // Find best value per primary metric for highlighting
                  const primaryMetric = metricNames[0];
                  const isBestRow =
                    hasHistory &&
                    experimentHistory.length > 1 &&
                    primaryMetric != null &&
                    record.metrics[primaryMetric] ===
                      Math.max(
                        ...experimentHistory.map(
                          (r) => r.metrics[primaryMetric] ?? -Infinity,
                        ),
                      );

                  return (
                    <TableRow key={i} className={isBestRow ? "bg-primary/5" : ""}>
                      <TableCell>
                        <Badge variant="outline" className="text-xs">
                          {record.iteration}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-medium">
                        {record.algorithm}
                        {isBestRow && (
                          <Badge variant="default" className="ml-2 text-xs">
                            Best
                          </Badge>
                        )}
                      </TableCell>
                      {metricNames.map((name) => (
                        <TableCell key={name} className="font-mono text-sm">
                          {record.metrics[name] != null
                            ? record.metrics[name].toFixed(4)
                            : "-"}
                        </TableCell>
                      ))}
                      <TableCell className="text-muted-foreground text-sm">
                        {record.training_time_seconds?.toFixed(1) ?? "-"}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        ) : (
          /* Fallback: raw JSON display for backward compatibility */
          <pre className="bg-muted overflow-x-auto rounded-md p-4 text-xs">
            {JSON.stringify(evaluation, null, 2)}
          </pre>
        )}
      </CardContent>
    </Card>
  );
}
