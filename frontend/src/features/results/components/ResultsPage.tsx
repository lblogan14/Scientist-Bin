import { Suspense, useEffect } from "react";
import { useParams } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, Download } from "lucide-react";
import { EmptyState } from "@/components/feedback/EmptyState";
import { ErrorBoundary } from "@/components/feedback/ErrorBoundary";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";
import { ExperimentSelector } from "@/components/shared/ExperimentSelector";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useExperimentIdSync } from "@/hooks/use-experiment-id-sync";
import {
  getArtifactDownloadUrl,
  getModelDownloadUrl,
  getResultsDownloadUrl,
  listExperiments,
} from "@/lib/api-client";
import { isExperimentError } from "@/types/api";
import type { ExperimentResult, ChartData } from "@/types/api";
import { useResult } from "../hooks/use-result";
import { getTabsForResult } from "../tab-registry";
import type { TabContext } from "../tab-registry";
import { ErrorDisplay } from "./ErrorDisplay";
import { MetricCards } from "./MetricCards";

export default function ResultsPage() {
  const params = useParams<{ id: string }>();
  const { experimentId, setExperimentId } = useExperimentIdSync();

  // Handle /results/:id deep-link route
  useEffect(() => {
    if (params.id && params.id !== experimentId) {
      setExperimentId(params.id);
    }
  }, [params.id, experimentId, setExperimentId]);

  // Auto-detect the latest completed/failed experiment when no ID is provided
  const { data: latestExperiment } = useQuery({
    queryKey: ["experiments", "latest-result"],
    queryFn: async () => {
      const { experiments: all } = await listExperiments();
      return (
        all.find((e) => e.status === "completed" || e.status === "failed") ??
        all[0] ??
        null
      );
    },
    enabled: !experimentId,
  });

  useEffect(() => {
    if (!experimentId && latestExperiment) {
      setExperimentId(latestExperiment.id);
    }
  }, [experimentId, latestExperiment, setExperimentId]);

  const { data, isLoading, isError } = useResult(experimentId);

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
  if (isError) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold">Results</h2>
        <ErrorDisplay error={`Failed to load experiment ${experimentId}.`} />
      </div>
    );
  }
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

  const successResult = isExperimentError(result)
    ? null
    : (result as ExperimentResult | null);
  const experimentHistory = successResult?.experiment_history ?? [];
  const evaluationResults = successResult?.evaluation_results as Record<
    string,
    unknown
  > | null;
  const bestMetrics =
    (evaluationResults?.metrics as Record<string, unknown>) ?? null;
  const chartData: ChartData | undefined =
    successResult?.report_sections?.chart_data;

  // Build the tab context
  const tabContext: TabContext = {
    result: successResult,
    chartData,
    experimentHistory,
    experimentId,
    experiment,
  };

  // Get available tabs for this problem type
  const tabs = getTabsForResult(successResult?.problem_type, tabContext);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold">Results</h2>
          <ExperimentSelector
            statusFilter={["completed", "failed"]}
            value={experimentId}
            onChange={setExperimentId}
            className="w-64"
          />
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
            <Button variant="outline" size="sm" asChild>
              <a href={getArtifactDownloadUrl(experimentId, "charts")} download>
                <Download className="mr-1 size-4" />
                Charts
              </a>
            </Button>
          </div>
        )}
      </div>

      {/* Top-level metric cards */}
      <MetricCards metrics={bestMetrics} />

      {/* Dynamic tabs driven by the tab registry */}
      <Tabs defaultValue={tabs[0]?.id ?? "overview"}>
        <TabsList className="flex-wrap">
          {tabs.map((tab) => (
            <TabsTrigger key={tab.id} value={tab.id}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        {tabs.map((tab) => (
          <TabsContent key={tab.id} value={tab.id} className="mt-4">
            <ErrorBoundary>
              <Suspense fallback={<LoadingSpinner message="Loading..." />}>
                <tab.component {...tabContext} />
              </Suspense>
            </ErrorBoundary>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
