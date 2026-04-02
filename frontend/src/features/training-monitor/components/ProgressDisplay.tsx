import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Experiment, ExperimentPhase } from "@/types/api";

interface ProgressDisplayProps {
  experiment: Experiment;
}

const PIPELINE_PHASES: { key: ExperimentPhase; label: string }[] = [
  { key: "initializing", label: "Init" },
  { key: "classify", label: "Classify" },
  { key: "eda", label: "EDA" },
  { key: "data_analysis", label: "Data" },
  { key: "planning", label: "Plan" },
  { key: "plan_review", label: "Review" },
  { key: "execution", label: "Execute" },
  { key: "analysis", label: "Analyze" },
  { key: "summarizing", label: "Summary" },
  { key: "done", label: "Done" },
];

function getPhaseIndex(phase: ExperimentPhase | null): number {
  if (!phase) return -1;
  const idx = PIPELINE_PHASES.findIndex((p) => p.key === phase);
  return idx === -1 ? -1 : idx;
}

export function ProgressDisplay({ experiment }: ProgressDisplayProps) {
  const isActive =
    experiment.status === "running" || experiment.status === "pending";
  const currentPhaseIdx = getPhaseIndex(experiment.phase);
  const iterationCount = experiment.iteration_count ?? 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Progress</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-3">
          {isActive && <Loader2 className="size-4 animate-spin" />}
          <Badge variant={isActive ? "default" : "outline"}>
            {experiment.status}
          </Badge>
          {experiment.phase && (
            <Badge variant="secondary">{experiment.phase}</Badge>
          )}
        </div>

        {/* Pipeline phase steps */}
        <div className="flex items-center gap-1">
          {PIPELINE_PHASES.map((phase, idx) => {
            const allDone =
              experiment.phase === "done" || experiment.status === "completed";
            const isCompleted = allDone || idx < currentPhaseIdx;
            const isCurrent = !allDone && idx === currentPhaseIdx;

            return (
              <div key={phase.key} className="flex items-center gap-1">
                {idx > 0 && (
                  <div
                    className={`h-0.5 w-4 ${isCompleted ? "bg-primary" : "bg-muted"}`}
                  />
                )}
                <div className="flex flex-col items-center gap-1">
                  {isCompleted ? (
                    <CheckCircle2 className="text-primary size-4" />
                  ) : isCurrent && phase.key === "plan_review" ? (
                    <Circle className="size-4 animate-pulse fill-amber-500/30 text-amber-500" />
                  ) : isCurrent ? (
                    <Loader2 className="text-primary size-4 animate-spin" />
                  ) : (
                    <Circle className="text-muted-foreground size-4" />
                  )}
                  <span
                    className={`text-xs ${isCurrent ? "text-primary font-medium" : isCompleted ? "text-primary" : "text-muted-foreground"}`}
                  >
                    {phase.label}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Iteration progress */}
        {iterationCount > 0 && (
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span>Iterations</span>
              <span className="font-medium">
                {iterationCount} / {5}
              </span>
            </div>
            <div className="bg-muted h-2 rounded-full">
              <div
                className="bg-primary h-2 rounded-full transition-all"
                style={{
                  width: `${Math.min((iterationCount / 5) * 100, 100)}%`,
                }}
              />
            </div>
          </div>
        )}

        <p className="text-sm">{experiment.objective}</p>
        <p className="text-muted-foreground text-xs">
          Started: {new Date(experiment.created_at).toLocaleString()}
        </p>
      </CardContent>
    </Card>
  );
}
