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
        </div>
        <Separator />
        <Button
          variant="destructive"
          size="sm"
          disabled={isPending}
          onClick={() =>
            remove(experimentId, { onSuccess: () => onDeleted() })
          }
        >
          {isPending ? "Deleting..." : "Delete Experiment"}
        </Button>
      </CardContent>
    </Card>
  );
}
