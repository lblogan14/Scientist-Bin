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
import { ClusterAnalysisTab } from "./ClusterAnalysisTab";
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
import { ResidualAnalysisTab } from "./ResidualAnalysisTab";
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
  const hasResiduals =
    (chartData?.residual_stats &&
      Object.keys(chartData.residual_stats).length > 0) ||
    experimentHistory.some((r) => r.residual_stats);
  const hasClusterStats =
    (chartData?.cluster_stats &&
      Object.keys(chartData.cluster_stats).length > 0) ||
    experimentHistory.some((r) => r.cluster_stats);

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
          {hasResiduals && (
            <TabsTrigger value="residuals">Residuals</TabsTrigger>
          )}
          {hasClusterStats && (
            <TabsTrigger value="clusters">Clusters</TabsTrigger>
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
          {successResult ? (
            <OverviewTab result={successResult} />
          ) : (
            <p className="text-muted-foreground text-sm">
              No results available.
            </p>
          )}
        </TabsContent>

        {/* Experiments (existing) */}
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

        {/* Confusion Matrix */}
        {hasConfusionMatrix && (
          <TabsContent value="confusion" className="mt-4">
            <ConfusionMatrixTab
              matrices={chartData?.confusion_matrices}
              history={experimentHistory}
            />
          </TabsContent>
        )}

        {/* Residual Analysis (regression) */}
        {hasResiduals && (
          <TabsContent value="residuals" className="mt-4">
            <ResidualAnalysisTab
              residualStats={chartData?.residual_stats}
              history={experimentHistory}
            />
          </TabsContent>
        )}

        {/* Cluster Analysis (clustering) */}
        {hasClusterStats && (
          <TabsContent value="clusters" className="mt-4">
            <ClusterAnalysisTab
              chartData={chartData}
              history={experimentHistory}
            />
          </TabsContent>
        )}

        {/* CV Stability */}
        {hasCVFolds && (
          <TabsContent value="cv-stability" className="mt-4">
            <CVStabilityTab chartData={chartData} history={experimentHistory} />
          </TabsContent>
        )}

        {/* Overfitting Analysis */}
        <TabsContent value="overfit" className="mt-4">
          <OverfitAnalysisTab history={experimentHistory} />
        </TabsContent>

        {/* Feature Importance */}
        {hasFeatureImportance && (
          <TabsContent value="features" className="mt-4">
            <FeatureImportanceTab
              chartData={chartData}
              history={experimentHistory}
            />
          </TabsContent>
        )}

        {/* Hyperparameters */}
        {hasHyperparamSearch && (
          <TabsContent value="hyperparams" className="mt-4">
            <HyperparameterTab
              chartData={chartData}
              history={experimentHistory}
              result={successResult ?? undefined}
            />
          </TabsContent>
        )}

        {/* Plan */}
        <TabsContent value="plan" className="mt-4">
          <PlanTab
            executionPlan={
              experiment.execution_plan ?? successResult?.plan ?? null
            }
            planMarkdown={successResult?.plan_markdown ?? null}
            experimentId={experimentId}
          />
        </TabsContent>

        {/* Analysis Report */}
        <TabsContent value="analysis" className="mt-4">
          <AnalysisTab
            analysisReport={
              experiment.analysis_report ??
              successResult?.analysis_report ??
              null
            }
            splitDataPaths={experiment.split_data_paths}
            experimentId={experimentId}
          />
        </TabsContent>

        {/* Summary Report */}
        <TabsContent value="summary" className="mt-4">
          <SummaryTab
            summaryReport={
              experiment.summary_report ?? successResult?.summary_report ?? null
            }
            sections={sections}
            experimentId={experimentId}
          />
        </TabsContent>

        {/* Code */}
        <TabsContent value="code" className="mt-4">
          <CodeDisplay code={successResult?.generated_code ?? null} />
        </TabsContent>

        {/* Data Profile */}
        {dataProfile && (
          <TabsContent value="data" className="mt-4">
            <DataProfileCard profile={dataProfile} />
          </TabsContent>
        )}

        {/* Journal */}
        <TabsContent value="journal" className="mt-4">
          <JournalViewer experimentId={experimentId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
