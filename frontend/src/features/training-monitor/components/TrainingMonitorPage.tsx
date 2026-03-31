import { useSearchParams } from "react-router";
import { Activity } from "lucide-react";
import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";
import { useTrainingStatus } from "../hooks/use-training-status";
import { useExperimentEvents } from "../hooks/use-experiment-events";
import { ProgressDisplay } from "./ProgressDisplay";
import { AgentActivityLog } from "./AgentActivityLog";
import { ConsoleOutput } from "./ConsoleOutput";
import { MetricsStream } from "./MetricsStream";

export default function TrainingMonitorPage() {
  const [searchParams] = useSearchParams();
  const experimentId = searchParams.get("id");

  const { data: experiment, isLoading } = useTrainingStatus(experimentId);
  const { activities, logLines, metrics, isConnected } =
    useExperimentEvents(experimentId);

  if (!experimentId) {
    return (
      <EmptyState
        icon={Activity}
        title="No experiment selected"
        description="Launch a training experiment from the Dashboard to see progress here."
      />
    );
  }

  if (isLoading) return <LoadingSpinner message="Loading experiment..." />;
  if (!experiment) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Training Monitor</h2>
        {isConnected && (
          <span className="flex items-center gap-2 text-sm text-green-600">
            <span className="size-2 animate-pulse rounded-full bg-green-500" />
            Live
          </span>
        )}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <ProgressDisplay experiment={experiment} />
        <AgentActivityLog activities={activities} />
      </div>
      {metrics.size > 0 && <MetricsStream metrics={metrics} />}
      <ConsoleOutput logs={logLines} />
    </div>
  );
}
