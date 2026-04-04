import {
  CheckCircle,
  Clock,
  FlaskConical,
  Loader2,
  TrendingUp,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { isExperimentError } from "@/types/api";
import type { ExperimentResult } from "@/types/api";
import { pickPrimaryMetric } from "@/lib/metric-utils";
import { useExperiments } from "../hooks/use-experiments";

export function DashboardStats() {
  const { data: experiments, isLoading } = useExperiments();

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="flex items-center gap-3 pt-6">
              <Skeleton className="size-5 rounded" />
              <div className="space-y-1.5">
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-6 w-12" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!experiments || experiments.length === 0) return null;

  const total = experiments.length;
  const completed = experiments.filter((e) => e.status === "completed");
  const completedCount = completed.length;
  const runningCount = experiments.filter((e) => e.status === "running").length;

  // Average best primary metric across completed experiments
  let avgBestScore: number | null = null;
  // Average training time
  let avgTrainingTime: number | null = null;
  if (completedCount > 0) {
    const scores: number[] = [];
    const times: number[] = [];
    for (const exp of completed) {
      const result = exp.result;
      if (!result || isExperimentError(result)) continue;
      const successResult = result as ExperimentResult;
      const problemType = successResult.problem_type ?? exp.problem_type;
      const history = successResult.experiment_history ?? [];
      for (const record of history) {
        if (record.metrics && Object.keys(record.metrics).length > 0) {
          const primary = pickPrimaryMetric(record.metrics, problemType);
          if (primary.value != null) {
            scores.push(primary.value);
            break;
          }
        }
      }
      const totalTime = history.reduce(
        (sum, r) => sum + (r.training_time_seconds ?? 0),
        0,
      );
      if (totalTime > 0) times.push(totalTime);
    }
    if (scores.length > 0) {
      avgBestScore = scores.reduce((a, b) => a + b, 0) / scores.length;
    }
    if (times.length > 0) {
      avgTrainingTime = times.reduce((a, b) => a + b, 0) / times.length;
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
      icon: Loader2,
      label: "Running",
      value: runningCount,
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
      label: "Avg Best Score",
      value: avgBestScore,
      format: (v: number) => v.toFixed(4),
    },
    {
      icon: Clock,
      label: "Avg Training Time",
      value: avgTrainingTime,
      format: (v: number) => `${v.toFixed(1)}s`,
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-5">
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
