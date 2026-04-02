import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface MetricCardsProps {
  metrics: Record<string, unknown> | null;
}

const RATIO_METRICS = new Set([
  "accuracy",
  "f1",
  "macro_f1",
  "micro_f1",
  "weighted_f1",
  "precision",
  "recall",
  "r2",
  "roc_auc",
  "silhouette_score",
]);

function getMetricColor(key: string, value: number): string {
  if (!RATIO_METRICS.has(key)) return "";
  // Silhouette score: range -1 to 1, different thresholds
  if (key === "silhouette_score") {
    if (value >= 0.5) return "text-success";
    if (value >= 0.25) return "text-warning";
    return "text-destructive";
  }
  if (value >= 0.9) return "text-success";
  if (value >= 0.7) return "text-warning";
  return "text-destructive";
}

function getBarColor(key: string, value: number): string {
  if (!RATIO_METRICS.has(key)) return "bg-primary";
  if (key === "silhouette_score") {
    if (value >= 0.5) return "bg-success";
    if (value >= 0.25) return "bg-warning";
    return "bg-destructive";
  }
  if (value >= 0.9) return "bg-success";
  if (value >= 0.7) return "bg-warning";
  return "bg-destructive";
}

function getBarWidth(key: string, value: number): number {
  // Silhouette score ranges from -1 to 1, normalize to 0-100%
  if (key === "silhouette_score") {
    return Math.min(Math.max((value + 1) * 50, 0), 100);
  }
  return Math.min(value * 100, 100);
}

export function MetricCards({ metrics }: MetricCardsProps) {
  if (!metrics || Object.keys(metrics).length === 0) {
    return null;
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Object.entries(metrics).map(([key, value]) => {
        const numVal = typeof value === "number" ? value : null;
        const isRatio = numVal !== null && RATIO_METRICS.has(key);

        return (
          <Card key={key}>
            <CardHeader className="pb-2">
              <CardTitle className="text-muted-foreground text-xs font-medium uppercase">
                {key}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p
                className={`text-2xl font-bold ${numVal !== null ? getMetricColor(key, numVal) : ""}`}
              >
                {numVal !== null ? numVal.toFixed(4) : String(value)}
              </p>
              {isRatio && numVal !== null && (
                <div className="bg-muted h-2 w-full overflow-hidden rounded-full">
                  <div
                    className={`h-full rounded-full transition-all ${getBarColor(key, numVal)}`}
                    style={{ width: `${getBarWidth(key, numVal)}%` }}
                  />
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
