import { CheckCircle, FlaskConical, TrendingUp } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { isExperimentError } from "@/types/api";
import { useExperiments } from "../hooks/use-experiments";

export function DashboardStats() {
  const { data: experiments } = useExperiments();

  if (!experiments || experiments.length === 0) return null;

  const total = experiments.length;
  const completed = experiments.filter((e) => e.status === "completed");
  const completedCount = completed.length;

  // Average best accuracy across completed experiments
  let avgBestAccuracy: number | null = null;
  if (completedCount > 0) {
    const accuracies: number[] = [];
    for (const exp of completed) {
      const result = exp.result;
      const history =
        result && !isExperimentError(result)
          ? result.experiment_history ?? []
          : [];
      for (const record of history) {
        const acc = record.metrics?.accuracy;
        if (acc != null) {
          accuracies.push(acc);
          break; // take first (best) per experiment
        }
      }
    }
    if (accuracies.length > 0) {
      avgBestAccuracy =
        accuracies.reduce((a, b) => a + b, 0) / accuracies.length;
    }
  }

  const stats = [
    {
      icon: FlaskConical,
      label: "Total Experiments",
      value: total,
      format: (v: number) => String(v),
    },
    {
      icon: CheckCircle,
      label: "Completed",
      value: completedCount,
      format: (v: number) => String(v),
    },
    {
      icon: TrendingUp,
      label: "Avg Best Accuracy",
      value: avgBestAccuracy,
      format: (v: number) => v.toFixed(4),
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-3">
      {stats.map(({ icon: Icon, label, value, format }) => (
        <Card key={label}>
          <CardContent className="flex items-center gap-3 pt-6">
            <Icon className="text-muted-foreground size-5" />
            <div>
              <p className="text-muted-foreground text-xs">{label}</p>
              <p className="text-xl font-bold">
                {value != null ? format(value) : "-"}
              </p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
