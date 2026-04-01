import { useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, Download } from "lucide-react";
import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  getModelDownloadUrl,
  getResultsDownloadUrl,
  listExperiments,
} from "@/lib/api-client";
import { isExperimentError } from "@/types/api";
import { useResult } from "../hooks/use-result";
import { AlgorithmComparisonChart } from "./AlgorithmComparisonChart";
import { AlgorithmRadarChart } from "./AlgorithmRadarChart";
import { CodeDisplay } from "./CodeDisplay";
import { DataProfileCard } from "./DataProfileCard";
import { ErrorDisplay } from "./ErrorDisplay";
import { EvaluationReport } from "./EvaluationReport";
import { JournalViewer } from "./JournalViewer";
import { MetricCards } from "./MetricCards";
import { TrainingTimeChart } from "./TrainingTimeChart";

export default function ResultsPage() {
  const [searchParams] = useSearchParams();
  const experimentIdParam = searchParams.get("id");
  const navigate = useNavigate();

  // Auto-detect the latest completed/failed experiment when no ID is provided
  const { data: latestExperiment } = useQuery({
    queryKey: ["experiments", "latest-result"],
    queryFn: async () => {
      const all = await listExperiments();
      return (
        all.find(
          (e) => e.status === "completed" || e.status === "failed",
        ) ??
        all[0] ??
        null
      );
    },
    enabled: !experimentIdParam,
  });

  useEffect(() => {
    if (!experimentIdParam && latestExperiment) {
      navigate(`/results?id=${latestExperiment.id}`, { replace: true });
    }
  }, [experimentIdParam, latestExperiment, navigate]);

  const experimentId = experimentIdParam ?? latestExperiment?.id ?? null;

  const { data, isLoading } = useResult(experimentId);

  if (!experimentId) {
    return (
      <EmptyState
        icon={BarChart3}
        title="No experiments yet"
        description="Launch a training experiment from the Dashboard to see results here."
      />
    );
  }

  if (isLoading) return <LoadingSpinner message="Loading results..." />;
  if (!data) return null;

  const { experiment, result } = data;

  // Handle failed experiments
  if (experiment.status === "failed" && isExperimentError(result)) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold">Results</h2>
        <ErrorDisplay error={result.error} traceback={result.traceback} />
      </div>
    );
  }

  const successResult = isExperimentError(result) ? null : result;
  const experimentHistory = successResult?.experiment_history ?? [];
  const dataProfile = successResult?.data_profile ?? null;
  const evaluationResults =
    successResult?.evaluation_results as Record<string, unknown> | null;
  const bestMetrics =
    (evaluationResults?.metrics as Record<string, unknown>) ?? null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold">Results</h2>
          {successResult?.problem_type && (
            <Badge variant="secondary">{successResult.problem_type}</Badge>
          )}
          {successResult?.iterations != null &&
            successResult.iterations > 0 && (
              <Badge variant="outline">
                {successResult.iterations} iterations
              </Badge>
            )}
        </div>
        {experiment.status === "completed" && (
          <div className="flex gap-2">
            <Button variant="outline" size="sm" asChild>
              <a href={getResultsDownloadUrl(experimentId)} download>
                <Download className="mr-1 size-4" />
                Results
              </a>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <a href={getModelDownloadUrl(experimentId)} download>
                <Download className="mr-1 size-4" />
                Model
              </a>
            </Button>
          </div>
        )}
      </div>

      {/* Best model metrics at the top */}
      <MetricCards metrics={bestMetrics} />

      <Tabs defaultValue="experiments">
        <TabsList>
          <TabsTrigger value="experiments">Experiments</TabsTrigger>
          <TabsTrigger value="code">Code</TabsTrigger>
          {dataProfile && <TabsTrigger value="data">Data Profile</TabsTrigger>}
          <TabsTrigger value="journal">Journal</TabsTrigger>
        </TabsList>

        <TabsContent value="experiments" className="mt-4 space-y-4">
          <EvaluationReport
            evaluation={evaluationResults}
            experimentHistory={experimentHistory}
          />
          <div className="grid gap-4 md:grid-cols-2">
            <AlgorithmComparisonChart history={experimentHistory} />
            <TrainingTimeChart history={experimentHistory} />
          </div>
          <AlgorithmRadarChart history={experimentHistory} />
        </TabsContent>

        <TabsContent value="code" className="mt-4">
          <CodeDisplay code={successResult?.generated_code ?? null} />
        </TabsContent>

        {dataProfile && (
          <TabsContent value="data" className="mt-4">
            <DataProfileCard profile={dataProfile} />
          </TabsContent>
        )}

        <TabsContent value="journal" className="mt-4">
          <JournalViewer experimentId={experimentId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
