import { Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Experiment } from "@/types/api";

interface ProgressDisplayProps {
  experiment: Experiment;
}

export function ProgressDisplay({ experiment }: ProgressDisplayProps) {
  const isActive =
    experiment.status === "running" || experiment.status === "pending";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Progress</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-3">
          {isActive && <Loader2 className="size-4 animate-spin" />}
          <Badge variant={isActive ? "default" : "outline"}>
            {experiment.status}
          </Badge>
        </div>
        <p className="text-sm">{experiment.objective}</p>
        <p className="text-muted-foreground text-xs">
          Started: {new Date(experiment.created_at).toLocaleString()}
        </p>
      </CardContent>
    </Card>
  );
}
