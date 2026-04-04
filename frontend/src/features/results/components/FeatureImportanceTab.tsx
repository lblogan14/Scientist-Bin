import { FeatureImportanceChart } from "@/components/charts/FeatureImportanceChart";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { ChartData, ExperimentRecord } from "@/types/api";

interface FeatureImportanceTabProps {
  chartData?: ChartData;
  history?: ExperimentRecord[];
}

export function FeatureImportanceTab({
  chartData,
  history,
}: FeatureImportanceTabProps) {
  // Primary source: chart_data from summary agent
  const fromChart = chartData?.feature_importances;
  // Fallback: latest experiment record with feature importances
  const fromHistory = history
    ?.filter((r) => r.feature_importances?.length)
    .at(-1);

  const algorithm = fromChart?.algorithm ?? fromHistory?.algorithm ?? "Unknown";
  const features =
    fromChart?.features ?? fromHistory?.feature_importances ?? [];

  if (features.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No feature importance data available for this experiment.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      <FeatureImportanceChart features={features} algorithm={algorithm} />

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">#</TableHead>
            <TableHead>Feature</TableHead>
            <TableHead className="text-right">Importance</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {features
            .sort((a, b) => b.importance - a.importance)
            .map((f, i) => (
              <TableRow key={f.feature}>
                <TableCell className="text-muted-foreground">{i + 1}</TableCell>
                <TableCell className="font-medium">
                  <span className="block max-w-[200px] truncate">{f.feature}</span>
                </TableCell>
                <TableCell className="text-right font-mono">
                  {f.importance.toFixed(4)}
                </TableCell>
              </TableRow>
            ))}
        </TableBody>
      </Table>
    </div>
  );
}
