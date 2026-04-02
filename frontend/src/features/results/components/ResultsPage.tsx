import { useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, Download } from "lucide-react";
import { EmptyState } from "@/components/feedback/EmptyState";
import { ErrorBoundary } from "@/components/feedback/ErrorBoundary";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  getArtifactDownloadUrl,
  getModelDownloadUrl,
  getResultsDownloadUrl,
  listExperiments,
} from "@/lib/api-client";
import { isExperimentError } from "@/types/api";
import type { ExperimentResult, ChartData } from "@/types/api";
import { useResult } from "../hooks/use-result";
import { AlgorithmComparisonChart } from "./AlgorithmComparisonChart";
import { AlgorithmRadarChart } from "./AlgorithmRadarChart";
import { AnalysisTab } from "./AnalysisTab";
import { CodeDisplay } from "./CodeDisplay";
import { ConfusionMatrixTab } from "./ConfusionMatrixTab";
import { CVStabilityTab } from "./CVStabilityTab";
import { DataProfileCard } from "./DataProfileCard";
import { ErrorDisplay } from "./ErrorDisplay";
import { EvaluationReport } from "./EvaluationReport";
import { FeatureImportanceTab } from "./FeatureImportanceTab";
import { HyperparameterTab } from "./HyperparameterTab";
import { JournalViewer } from "./JournalViewer";
import { MetricCards } from "./MetricCards";
import { OverfitAnalysisTab } from "./OverfitAnalysisTab";
import { OverviewTab } from "./OverviewTab";
import { PlanTab } from "./PlanTab";
import { SummaryTab } from "./SummaryTab";
import { TrainingTimeChart } from "./TrainingTimeChart";

export default function ResultsPage() {
  const [searchParams] = useSearchParams();
  const experimentIdParam = searchParams.get("id");
  const navigate = useNavigate();

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
    enabled: !experimentIdParam,
  });

  useEffect(() => {
    if (!experimentIdParam && latestExperiment) {
      navigate(`/results?id=${latestExperiment.id}`, { replace: true });
    }
  }, [experimentIdParam, latestExperiment, navigate]);

  const experimentId = experimentIdParam ?? latestExperiment?.id ?? null;

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
  const dataProfile = successResult?.data_profile ?? null;
  const evaluationResults = successResult?.evaluation_results as Record<
    string,
    unknown
  > | null;
  const bestMetrics =
    (evaluationResults?.metrics as Record<string, unknown>) ?? null;
  const chartData: ChartData | undefined =
    successResult?.report_sections?.chart_data;
  const sections = successResult?.report_sections ?? null;

  // Determine which diagnostic tabs have data
  const hasConfusionMatrix =
    (chartData?.confusion_matrices &&
      Object.keys(chartData.confusion_matrices).length > 0) ||
    experimentHistory.some((r) => r.confusion_matrix);
  const hasCVFolds =
    (chartData?.cv_fold_scores &&
      Object.keys(chartData.cv_fold_scores).length > 0) ||
    experimentHistory.some((r) => r.cv_fold_scores);
  const hasFeatureImportance =
    chartData?.feature_importances?.features?.length ||
    experimentHistory.some((r) => r.feature_importances?.length);
  const hasHyperparamSearch =
    (chartData?.hyperparam_search &&
      Object.keys(chartData.hyperparam_search).length > 0) ||
    experimentHistory.some((r) => r.cv_results_top_n?.length);

  return (
    <div className="space-y-6">
      {/* Header */}
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

      {/* Three-group tab layout: Overview | Analysis | Reports */}
      <Tabs defaultValue="overview">
        <TabsList className="flex-wrap">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="experiments">Experiments</TabsTrigger>
          {hasConfusionMatrix && (
            <TabsTrigger value="confusion">Confusion Matrix</TabsTrigger>
          )}
          {hasCVFolds && (
            <TabsTrigger value="cv-stability">CV Stability</TabsTrigger>
          )}
          <TabsTrigger value="overfit">Overfitting</TabsTrigger>
          {hasFeatureImportance && (
            <TabsTrigger value="features">Features</TabsTrigger>
          )}
          {hasHyperparamSearch && (
            <TabsTrigger value="hyperparams">Hyperparams</TabsTrigger>
          )}
          <TabsTrigger value="plan">Plan</TabsTrigger>
          <TabsTrigger value="analysis">Analysis</TabsTrigger>
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="code">Code</TabsTrigger>
          {dataProfile && <TabsTrigger value="data">Data</TabsTrigger>}
          <TabsTrigger value="journal">Journal</TabsTrigger>
        </TabsList>

        {/* Overview */}
        <TabsContent value="overview" className="mt-4">
          <ErrorBoundary>
            {successResult ? (
              <OverviewTab result={successResult} />
            ) : (
              <p className="text-muted-foreground text-sm">
                No results available.
              </p>
            )}
          </ErrorBoundary>
        </TabsContent>

        {/* Experiments (existing) */}
        <TabsContent value="experiments" className="mt-4 space-y-4">
          <ErrorBoundary>
            <EvaluationReport
              evaluation={evaluationResults}
              experimentHistory={experimentHistory}
            />
            <div className="grid gap-4 md:grid-cols-2">
              <AlgorithmComparisonChart history={experimentHistory} />
              <TrainingTimeChart history={experimentHistory} />
            </div>
            <AlgorithmRadarChart history={experimentHistory} />
          </ErrorBoundary>
        </TabsContent>

        {/* Confusion Matrix */}
        {hasConfusionMatrix && (
          <TabsContent value="confusion" className="mt-4">
            <ErrorBoundary>
              <ConfusionMatrixTab
                matrices={chartData?.confusion_matrices}
                history={experimentHistory}
              />
            </ErrorBoundary>
          </TabsContent>
        )}

        {/* CV Stability */}
        {hasCVFolds && (
          <TabsContent value="cv-stability" className="mt-4">
            <ErrorBoundary>
              <CVStabilityTab
                chartData={chartData}
                history={experimentHistory}
              />
            </ErrorBoundary>
          </TabsContent>
        )}

        {/* Overfitting Analysis */}
        <TabsContent value="overfit" className="mt-4">
          <ErrorBoundary>
            <OverfitAnalysisTab history={experimentHistory} />
          </ErrorBoundary>
        </TabsContent>

        {/* Feature Importance */}
        {hasFeatureImportance && (
          <TabsContent value="features" className="mt-4">
            <ErrorBoundary>
              <FeatureImportanceTab
                chartData={chartData}
                history={experimentHistory}
              />
            </ErrorBoundary>
          </TabsContent>
        )}

        {/* Hyperparameters */}
        {hasHyperparamSearch && (
          <TabsContent value="hyperparams" className="mt-4">
            <ErrorBoundary>
              <HyperparameterTab
                chartData={chartData}
                history={experimentHistory}
                result={successResult ?? undefined}
              />
            </ErrorBoundary>
          </TabsContent>
        )}

        {/* Plan */}
        <TabsContent value="plan" className="mt-4">
          <ErrorBoundary>
            <PlanTab
              executionPlan={
                experiment.execution_plan ?? successResult?.plan ?? null
              }
              planMarkdown={successResult?.plan_markdown ?? null}
              experimentId={experimentId}
            />
          </ErrorBoundary>
        </TabsContent>

        {/* Analysis Report */}
        <TabsContent value="analysis" className="mt-4">
          <ErrorBoundary>
            <AnalysisTab
              analysisReport={
                experiment.analysis_report ??
                successResult?.analysis_report ??
                null
              }
              splitDataPaths={experiment.split_data_paths}
              experimentId={experimentId}
            />
          </ErrorBoundary>
        </TabsContent>

        {/* Summary Report */}
        <TabsContent value="summary" className="mt-4">
          <ErrorBoundary>
            <SummaryTab
              summaryReport={
                experiment.summary_report ??
                successResult?.summary_report ??
                null
              }
              sections={sections}
              experimentId={experimentId}
            />
          </ErrorBoundary>
        </TabsContent>

        {/* Code */}
        <TabsContent value="code" className="mt-4">
          <ErrorBoundary>
            <CodeDisplay code={successResult?.generated_code ?? null} />
          </ErrorBoundary>
        </TabsContent>

        {/* Data Profile */}
        {dataProfile && (
          <TabsContent value="data" className="mt-4">
            <ErrorBoundary>
              <DataProfileCard profile={dataProfile} />
            </ErrorBoundary>
          </TabsContent>
        )}

        {/* Journal */}
        <TabsContent value="journal" className="mt-4">
          <ErrorBoundary>
            <JournalViewer experimentId={experimentId} />
          </ErrorBoundary>
        </TabsContent>
      </Tabs>
    </div>
  );
}
