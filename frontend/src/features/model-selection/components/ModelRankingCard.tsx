import { Award } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Experiment, ExperimentResult } from "@/types/api";
import { isExperimentError } from "@/types/api";

interface ModelRankingCardProps {
  models: Experiment[];
}

export function ModelRankingCard({ models }: ModelRankingCardProps) {
  // Extract best model info per completed experiment
  const rankings = models
    .filter((m) => m.result && !isExperimentError(m.result))
    .map((m) => {
      const result = m.result as ExperimentResult;
      const bestRecord = result.experiment_history?.find(
        (h) => h.algorithm === result.best_model,
      );
      // Find primary metric (first val_ metric, then first metric)
      const metrics = bestRecord?.metrics ?? {};
      const primaryKey =
        Object.keys(metrics).find((k) => k.startsWith("val_")) ??
        Object.keys(metrics)[0];
      const primaryValue = primaryKey ? metrics[primaryKey] : null;
      return {
        id: m.id,
        objective: m.objective,
        algorithm: result.best_model ?? "Unknown",
        primaryMetric: primaryKey ?? "",
        primaryValue,
        reasoning: result.selection_reasoning,
        trainingTime: bestRecord?.training_time_seconds ?? 0,
      };
    })
    .sort((a, b) => (b.primaryValue ?? 0) - (a.primaryValue ?? 0));

  if (rankings.length === 0) return null;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {rankings.slice(0, 6).map((r, idx) => (
        <Card
          key={r.id}
          className={idx === 0 ? "border-primary/30 bg-primary/5" : ""}
        >
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              {idx === 0 && <Award className="text-primary size-4" />}
              <span className="text-muted-foreground">#{idx + 1}</span>
              {r.algorithm}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <p className="text-muted-foreground truncate text-xs">
              {r.objective}
            </p>
            {r.primaryValue != null && (
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold">
                  {r.primaryValue.toFixed(4)}
                </span>
                <Badge variant="outline" className="text-xs">
                  {r.primaryMetric}
                </Badge>
              </div>
            )}
            <p className="text-muted-foreground text-xs">
              {r.trainingTime.toFixed(1)}s training time
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
