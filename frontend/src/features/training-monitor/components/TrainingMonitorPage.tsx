import { useEffect } from "react";
import { useSearchParams, Link, useNavigate } from "react-router";
import { HTTPError } from "ky";
import { Activity, AlertCircle } from "lucide-react";
import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";
import { Button } from "@/components/ui/button";
import { useTrainingStatus } from "../hooks/use-training-status";
import { useExperimentEvents } from "../hooks/use-experiment-events";
import { ProgressDisplay } from "./ProgressDisplay";
import { AgentActivityLog } from "./AgentActivityLog";
import { ConsoleOutput } from "./ConsoleOutput";
import { MetricsStream } from "./MetricsStream";

export default function TrainingMonitorPage() {
  const [searchParams] = useSearchParams();
  const experimentId = searchParams.get("id");
  const navigate = useNavigate();

  const {
    data: experiment,
    isLoading,
    isError,
    error,
  } = useTrainingStatus(experimentId);

  const isNotFound =
    isError && error instanceof HTTPError && error.response.status === 404;

  const { activities, logLines, metrics, isConnected, isDone } =
    useExperimentEvents(experimentId, !isNotFound);

  useEffect(() => {
    if (isDone && experimentId) {
      const timer = setTimeout(() => {
        navigate(`/results?id=${experimentId}`);
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [isDone, experimentId, navigate]);

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

  if (isNotFound) {
    return (
      <EmptyState
        icon={AlertCircle}
        title="Experiment not found"
        description="This experiment may have been removed when the server restarted. Start a new experiment from the Dashboard."
        action={
          <Button asChild variant="outline">
            <Link to="/">Back to Dashboard</Link>
          </Button>
        }
      />
    );
  }

  if (isError) {
    return (
      <EmptyState
        icon={AlertCircle}
        title="Failed to load experiment"
        description={error?.message ?? "An unexpected error occurred."}
        action={
          <Button asChild variant="outline">
            <Link to="/">Back to Dashboard</Link>
          </Button>
        }
      />
    );
  }

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
