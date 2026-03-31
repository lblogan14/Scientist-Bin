import { useSearchParams } from "react-router";
import { Activity } from "lucide-react";
import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";
import { useTrainingStatus } from "../hooks/use-training-status";
import { ProgressDisplay } from "./ProgressDisplay";
import { AgentActivityLog } from "./AgentActivityLog";
import { ConsoleOutput } from "./ConsoleOutput";

export default function TrainingMonitorPage() {
  const [searchParams] = useSearchParams();
  const experimentId = searchParams.get("id");

  const { data: experiment, isLoading } = useTrainingStatus(experimentId);

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
      <h2 className="text-2xl font-bold">Training Monitor</h2>
      <div className="grid gap-6 lg:grid-cols-2">
        <ProgressDisplay experiment={experiment} />
        <AgentActivityLog activities={[]} />
      </div>
      <ConsoleOutput logs={[]} />
    </div>
  );
}
