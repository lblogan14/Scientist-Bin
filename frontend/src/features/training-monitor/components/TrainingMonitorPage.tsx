import { useEffect, useMemo } from "react";
import { useSearchParams, Link, useNavigate } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { HTTPError } from "ky";
import { Activity, AlertCircle } from "lucide-react";
import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";
import { Button } from "@/components/ui/button";
import { listExperiments } from "@/lib/api-client";
import type { AgentActivity, ProgressEvent } from "@/types/api";
import { isExperimentError } from "@/types/api";
import { ErrorDisplay } from "../../results/components/ErrorDisplay";
import { useTrainingStatus } from "../hooks/use-training-status";
import { useExperimentEvents } from "../hooks/use-experiment-events";
import { ProgressDisplay } from "./ProgressDisplay";
import { AgentActivityLog } from "./AgentActivityLog";
import { ConsoleOutput } from "./ConsoleOutput";
import { MetricsStream } from "./MetricsStream";
import { PlanReviewPanel } from "./PlanReviewPanel";

export default function TrainingMonitorPage() {
  const [searchParams] = useSearchParams();
  const experimentIdParam = searchParams.get("id");
  const navigate = useNavigate();

  // Auto-detect the latest running/pending experiment when no ID is provided
  const { data: latestExperiment } = useQuery({
    queryKey: ["experiments", "latest-active"],
    queryFn: async () => {
      const { experiments: all } = await listExperiments();
      return (
        all.find((e) => e.status === "running" || e.status === "pending") ??
        all[0] ??
        null
      );
    },
    enabled: !experimentIdParam,
  });

  // Redirect to the latest experiment if found
  useEffect(() => {
    if (!experimentIdParam && latestExperiment) {
      navigate(`/monitor?id=${latestExperiment.id}`, { replace: true });
    }
  }, [experimentIdParam, latestExperiment, navigate]);

  const experimentId = experimentIdParam ?? latestExperiment?.id ?? null;

  const {
    data: experiment,
    isLoading,
    isError,
    error,
  } = useTrainingStatus(experimentId);

  const isNotFound =
    isError && error instanceof HTTPError && error.response.status === 404;

  const { activities, logLines, metrics, isConnected, isDone, planReview } =
    useExperimentEvents(experimentId, !isNotFound);

  // Use SSE activities when live, fall back to stored progress_events.
  // This hook must be before any early returns to satisfy React's rules of hooks.
  const storedEvents = experiment?.progress_events;
  const displayActivities = useMemo(() => {
    if (activities.length > 0) return activities;
    if (!storedEvents?.length) return [];

    return storedEvents
      .filter(
        (e: ProgressEvent) =>
          e.event_type !== "metric_update" && e.event_type !== "log_output",
      )
      .map((e: ProgressEvent): AgentActivity => {
        const data = e.data;
        let action: string = e.event_type;
        let details: string | undefined;

        if (e.event_type === "phase_change") {
          action = `Phase: ${data.phase ?? "unknown"}`;
          details = data.message as string | undefined;
        } else if (e.event_type === "agent_activity") {
          action = (data.action as string) ?? "activity";
          details = data.decision as string | undefined;
        } else if (e.event_type === "run_started") {
          action = "Training started";
          details = `Run ${data.run_id}`;
        } else if (e.event_type === "run_completed") {
          action = `Run ${data.status}`;
          details = `${data.wall_time_seconds}s`;
        } else if (e.event_type === "experiment_done") {
          action = "Experiment complete";
          details = data.best_model
            ? `Best model: ${data.best_model}`
            : undefined;
        } else if (e.event_type === "error") {
          action = "Error";
          details = data.message as string | undefined;
        }

        return {
          agent: "sklearn",
          action,
          timestamp: e.timestamp,
          details,
          data,
        };
      });
  }, [activities, storedEvents]);

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

  const hasFailed =
    experiment.status === "failed" && isExperimentError(experiment.result);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Training</h2>
        {isConnected && (
          <span className="flex items-center gap-2 text-sm text-success">
            <span className="size-2 animate-pulse rounded-full bg-success" />
            Live
          </span>
        )}
      </div>
      {hasFailed && isExperimentError(experiment.result) && (
        <ErrorDisplay
          error={experiment.result.error}
          traceback={experiment.result.traceback}
        />
      )}
      {/* Plan review UI — show when phase is plan_review or SSE sent plan_review_pending */}
      {(experiment.phase === "plan_review" || planReview) &&
        experimentId &&
        planReview && (
          <PlanReviewPanel
            experimentId={experimentId}
            planMarkdown={planReview.planMarkdown}
            revisionCount={planReview.revisionCount}
          />
        )}
      <div className="grid gap-6 lg:grid-cols-2">
        <ProgressDisplay experiment={experiment} />
        <AgentActivityLog activities={displayActivities} />
      </div>
      {metrics.size > 0 && <MetricsStream metrics={metrics} />}
      <ConsoleOutput logs={logLines} />
    </div>
  );
}
