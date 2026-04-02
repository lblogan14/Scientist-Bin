import { Link } from "react-router";
import { Activity, BarChart3, FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useExperiment } from "../hooks/use-experiment";
import { useDeleteExperiment } from "../hooks/use-delete-experiment";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";

interface ExperimentDetailProps {
  experimentId: string;
  onDeleted: () => void;
}

export function ExperimentDetail({
  experimentId,
  onDeleted,
}: ExperimentDetailProps) {
  const { data: experiment, isLoading } = useExperiment(experimentId);
  const { mutate: remove, isPending } = useDeleteExperiment();

  if (isLoading) return <LoadingSpinner />;
  if (!experiment) return null;

  const isActive =
    experiment.status === "running" || experiment.status === "pending";
  const isCompleted = experiment.status === "completed";

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base">{experiment.objective}</CardTitle>
        <Badge variant="outline">{experiment.status}</Badge>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-2 text-sm">
          <span className="text-muted-foreground">Framework</span>
          <span>{experiment.framework ?? "Auto-detect"}</span>
          <span className="text-muted-foreground">Created</span>
          <span>{new Date(experiment.created_at).toLocaleString()}</span>
          <span className="text-muted-foreground">Data</span>
          <span>{experiment.data_description || "Not specified"}</span>
          {experiment.data_file_path && (
            <>
              <span className="text-muted-foreground">Data File</span>
              <span className="truncate font-mono text-xs">
                {experiment.data_file_path}
              </span>
            </>
          )}
          {experiment.phase && (
            <>
              <span className="text-muted-foreground">Current Phase</span>
              <Badge variant="secondary" className="w-fit">
                {experiment.phase}
              </Badge>
            </>
          )}
          {experiment.iteration_count > 0 && (
            <>
              <span className="text-muted-foreground">Iterations</span>
              <span>{experiment.iteration_count}</span>
            </>
          )}
        </div>

        {/* Execution plan summary */}
        {experiment.execution_plan && (
          <>
            <Separator />
            <div className="space-y-1">
              <span className="text-muted-foreground text-xs font-medium">
                Execution Plan
              </span>
              <div className="flex flex-wrap gap-1">
                {(
                  (experiment.execution_plan as Record<string, unknown>)
                    .algorithms_to_try as string[] | undefined
                )?.map((algo, i) => (
                  <Badge key={i} variant="outline" className="text-xs">
                    {algo}
                  </Badge>
                ))}
              </div>
            </div>
          </>
        )}

        <Separator />

        <div className="flex flex-wrap gap-2">
          {isActive && (
            <Button variant="outline" size="sm" asChild>
              <Link to={`/monitor?id=${experimentId}`}>
                <Activity className="mr-1.5 size-3.5" />
                Monitor
              </Link>
            </Button>
          )}
          {isCompleted && (
            <Button variant="outline" size="sm" asChild>
              <Link to={`/results?id=${experimentId}`}>
                <BarChart3 className="mr-1.5 size-3.5" />
                View Results
              </Link>
            </Button>
          )}
          {experiment.analysis_report && (
            <Button variant="ghost" size="sm" asChild>
              <Link to={`/results?id=${experimentId}`}>
                <FileText className="mr-1.5 size-3.5" />
                Analysis
              </Link>
            </Button>
          )}
          <Button
            variant="destructive"
            size="sm"
            disabled={isPending}
            onClick={() =>
              remove(experimentId, { onSuccess: () => onDeleted() })
            }
          >
            {isPending ? "Deleting..." : "Delete"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
