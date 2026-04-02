import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { OverfitGaugeChart } from "@/components/charts/OverfitGaugeChart";
import type { ExperimentRecord, OverfitEntry } from "@/types/api";

interface OverfitAnalysisTabProps {
  entries?: OverfitEntry[];
  history?: ExperimentRecord[];
}

function riskBadge(risk: string) {
  switch (risk) {
    case "low":
      return <Badge className="bg-success/15 text-success">Low</Badge>;
    case "moderate":
      return <Badge className="bg-warning/15 text-warning">Moderate</Badge>;
    case "high":
      return <Badge className="bg-destructive/15 text-destructive">High</Badge>;
    default:
      return <Badge variant="outline">{risk}</Badge>;
  }
}

/** Derive overfit entries from experiment history if not provided by diagnostics */
function deriveEntries(history: ExperimentRecord[]): OverfitEntry[] {
  const entries: OverfitEntry[] = [];
  for (const rec of history) {
    for (const [key, val] of Object.entries(rec.metrics)) {
      if (!key.startsWith("train_")) continue;
      const metricName = key.replace("train_", "");
      const valKey = `val_${metricName}`;
      const valVal = rec.metrics[valKey];
      if (valVal == null) continue;
      const gap = val - valVal;
      const gapPct = val > 0 ? (gap / val) * 100 : 0;
      let risk: "low" | "moderate" | "high" = "low";
      if (gapPct > 10) risk = "high";
      else if (gapPct > 5) risk = "moderate";
      entries.push({
        algorithm: rec.algorithm,
        metric_name: metricName,
        train_value: val,
        val_value: valVal,
        gap,
        gap_percentage: gapPct,
        overfit_risk: risk,
      });
    }
  }
  return entries;
}

export function OverfitAnalysisTab({
  entries,
  history,
}: OverfitAnalysisTabProps) {
  const data = entries?.length ? entries : deriveEntries(history ?? []);

  if (data.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No overfitting analysis data available. Train/validation metric pairs
        are needed.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      <OverfitGaugeChart entries={data} />

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Algorithm</TableHead>
            <TableHead>Metric</TableHead>
            <TableHead className="text-right">Train</TableHead>
            <TableHead className="text-right">Validation</TableHead>
            <TableHead className="text-right">Gap</TableHead>
            <TableHead className="text-right">Gap %</TableHead>
            <TableHead>Risk</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((e, i) => (
            <TableRow key={i}>
              <TableCell className="font-medium">{e.algorithm}</TableCell>
              <TableCell>{e.metric_name}</TableCell>
              <TableCell className="text-right font-mono">
                {e.train_value.toFixed(4)}
              </TableCell>
              <TableCell className="text-right font-mono">
                {e.val_value.toFixed(4)}
              </TableCell>
              <TableCell className="text-right font-mono">
                {e.gap.toFixed(4)}
              </TableCell>
              <TableCell className="text-right font-mono">
                {e.gap_percentage.toFixed(1)}%
              </TableCell>
              <TableCell>{riskBadge(e.overfit_risk)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
