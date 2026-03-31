import { useSearchParams } from "react-router";
import { BarChart3 } from "lucide-react";
import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";
import { useResult } from "../hooks/use-result";
import { CodeDisplay } from "./CodeDisplay";
import { MetricCards } from "./MetricCards";
import { EvaluationReport } from "./EvaluationReport";

export default function ResultsPage() {
  const [searchParams] = useSearchParams();
  const experimentId = searchParams.get("id");

  const { data, isLoading } = useResult(experimentId);

  if (!experimentId) {
    return (
      <EmptyState
        icon={BarChart3}
        title="No experiment selected"
        description="Select an experiment from the Experiments page to view results."
      />
    );
  }

  if (isLoading) return <LoadingSpinner message="Loading results..." />;
  if (!data) return null;

  const { result } = data;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Results</h2>
      <MetricCards
        metrics={
          result?.evaluation_results as Record<string, unknown> | null
        }
      />
      <CodeDisplay code={result?.generated_code ?? null} />
      <EvaluationReport
        evaluation={
          result?.evaluation_results as Record<string, unknown> | null
        }
      />
    </div>
  );
}
