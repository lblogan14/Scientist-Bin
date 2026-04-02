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
]);

function getMetricColor(key: string, value: number): string {
  if (!RATIO_METRICS.has(key)) return "";
  if (value >= 0.9) return "text-success";
  if (value >= 0.7) return "text-warning";
  return "text-destructive";
}

function getBarColor(key: string, value: number): string {
  if (!RATIO_METRICS.has(key)) return "bg-primary";
  if (value >= 0.9) return "bg-success";
  if (value >= 0.7) return "bg-warning";
  return "bg-destructive";
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
                    style={{ width: `${Math.min(numVal * 100, 100)}%` }}
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
