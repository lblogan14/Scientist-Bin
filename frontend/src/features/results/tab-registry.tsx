/**
 * Tab Registry — maps problem_type to available Results page tabs.
 *
 * Adding a new task type requires only adding entries here, not modifying
 * the ResultsPage component itself.
 */

import type { ComponentType } from "react";
import type {
  ChartData,
  Experiment,
  ExperimentRecord,
  ExperimentResult,
} from "@/types/api";

// ---------------------------------------------------------------------------
// Unified context passed to every tab
// ---------------------------------------------------------------------------

export interface TabContext {
  result: ExperimentResult | null;
  chartData?: ChartData;
  experimentHistory: ExperimentRecord[];
  experimentId: string;
  experiment: Experiment;
}

// ---------------------------------------------------------------------------
// Tab definition
// ---------------------------------------------------------------------------

export interface TabDefinition {
  id: string;
  label: string;
  /** The React component rendered inside <TabsContent> */
  component: ComponentType<TabContext>;
  /** Return true when there is enough data to show this tab */
  isAvailable: (ctx: TabContext) => boolean;
  /** Lower = further left */
  order: number;
}

// ---------------------------------------------------------------------------
// Lazy imports for tab components (keeps the bundle lean)
// ---------------------------------------------------------------------------

import { lazy } from "react";

// Common tabs (always available)
const OverviewTabAdapter = lazy(() =>
  import("./components/OverviewTabAdapter").then((m) => ({
    default: m.OverviewTabAdapter,
  })),
);
const ExperimentsTab = lazy(() =>
  import("./components/ExperimentsTab").then((m) => ({
    default: m.ExperimentsTab,
  })),
);
const PlanTabAdapter = lazy(() =>
  import("./components/PlanTabAdapter").then((m) => ({
    default: m.PlanTabAdapter,
  })),
);
const AnalysisTabAdapter = lazy(() =>
  import("./components/AnalysisTabAdapter").then((m) => ({
    default: m.AnalysisTabAdapter,
  })),
);
const SummaryTabAdapter = lazy(() =>
  import("./components/SummaryTabAdapter").then((m) => ({
    default: m.SummaryTabAdapter,
  })),
);
const CodeTab = lazy(() =>
  import("./components/CodeTab").then((m) => ({ default: m.CodeTab })),
);
const DataTab = lazy(() =>
  import("./components/DataTab").then((m) => ({ default: m.DataTab })),
);
const JournalTab = lazy(() =>
  import("./components/JournalTab").then((m) => ({ default: m.JournalTab })),
);

// Classification-specific
const ConfusionMatrixTabWrapper = lazy(() =>
  import("./components/ConfusionMatrixTabWrapper").then((m) => ({
    default: m.ConfusionMatrixTabWrapper,
  })),
);
const CVStabilityTabWrapper = lazy(() =>
  import("./components/CVStabilityTabWrapper").then((m) => ({
    default: m.CVStabilityTabWrapper,
  })),
);
const OverfitTabWrapper = lazy(() =>
  import("./components/OverfitTabWrapper").then((m) => ({
    default: m.OverfitTabWrapper,
  })),
);
const FeatureTabWrapper = lazy(() =>
  import("./components/FeatureTabWrapper").then((m) => ({
    default: m.FeatureTabWrapper,
  })),
);
const HyperparamTabWrapper = lazy(() =>
  import("./components/HyperparamTabWrapper").then((m) => ({
    default: m.HyperparamTabWrapper,
  })),
);

// Clustering-specific
const ClusterScatterTab = lazy(() =>
  import("./components/ClusterScatterTab").then((m) => ({
    default: m.ClusterScatterTab,
  })),
);
const ElbowCurveTab = lazy(() =>
  import("./components/ElbowCurveTab").then((m) => ({
    default: m.ElbowCurveTab,
  })),
);
const SilhouetteTab = lazy(() =>
  import("./components/SilhouetteTab").then((m) => ({
    default: m.SilhouetteTab,
  })),
);
const ClusterProfileTab = lazy(() =>
  import("./components/ClusterProfileTab").then((m) => ({
    default: m.ClusterProfileTab,
  })),
);

// FLAML / Time series-specific
const ForecastPlotTab = lazy(() =>
  import("./components/ForecastPlotTab").then((m) => ({
    default: m.ForecastPlotTab,
  })),
);
const TrialHistoryTab = lazy(() =>
  import("./components/TrialHistoryTab").then((m) => ({
    default: m.TrialHistoryTab,
  })),
);
const EstimatorComparisonTab = lazy(() =>
  import("./components/EstimatorComparisonTab").then((m) => ({
    default: m.EstimatorComparisonTab,
  })),
);

// Regression-specific
const ActualVsPredictedTab = lazy(() =>
  import("./components/ActualVsPredictedTab").then((m) => ({
    default: m.ActualVsPredictedTab,
  })),
);
const ResidualPlotTab = lazy(() =>
  import("./components/ResidualPlotTab").then((m) => ({
    default: m.ResidualPlotTab,
  })),
);
const CoefficientTab = lazy(() =>
  import("./components/CoefficientTab").then((m) => ({
    default: m.CoefficientTab,
  })),
);
const LearningCurveTab = lazy(() =>
  import("./components/LearningCurveTab").then((m) => ({
    default: m.LearningCurveTab,
  })),
);

// ---------------------------------------------------------------------------
// Availability helpers
// ---------------------------------------------------------------------------

function hasConfusionMatrix(ctx: TabContext): boolean {
  const cd = ctx.chartData;
  return !!(
    (cd?.confusion_matrices &&
      Object.keys(cd.confusion_matrices).length > 0) ||
    ctx.experimentHistory.some((r) => r.confusion_matrix)
  );
}

function hasCVFolds(ctx: TabContext): boolean {
  const cd = ctx.chartData;
  return !!(
    (cd?.cv_fold_scores && Object.keys(cd.cv_fold_scores).length > 0) ||
    ctx.experimentHistory.some((r) => r.cv_fold_scores)
  );
}

function hasFeatureImportance(ctx: TabContext): boolean {
  const cd = ctx.chartData;
  return !!(
    cd?.feature_importances?.features?.length ||
    ctx.experimentHistory.some((r) => r.feature_importances?.length)
  );
}

function hasHyperparamSearch(ctx: TabContext): boolean {
  const cd = ctx.chartData;
  return !!(
    (cd?.hyperparam_search && Object.keys(cd.hyperparam_search).length > 0) ||
    ctx.experimentHistory.some((r) => r.cv_results_top_n?.length)
  );
}

function hasClusterScatter(ctx: TabContext): boolean {
  return !!(
    ctx.chartData?.cluster_scatter?.length ||
    ctx.experimentHistory.some((r) => r.cluster_scatter?.length)
  );
}

function hasElbowData(ctx: TabContext): boolean {
  return !!(
    ctx.chartData?.elbow_curve?.length ||
    ctx.experimentHistory.some((r) => r.elbow_data?.length)
  );
}

function hasSilhouetteData(ctx: TabContext): boolean {
  return !!(
    ctx.chartData?.silhouette_data?.length ||
    ctx.experimentHistory.some((r) => r.silhouette_per_sample?.length)
  );
}

function hasClusterProfiles(ctx: TabContext): boolean {
  return !!(
    ctx.chartData?.cluster_profiles?.length ||
    ctx.experimentHistory.some((r) => r.cluster_profiles?.length)
  );
}

function hasActualVsPredicted(ctx: TabContext): boolean {
  return !!(
    ctx.chartData?.actual_vs_predicted?.length ||
    ctx.experimentHistory.some((r) => r.actual_vs_predicted?.length)
  );
}

function hasResidualStats(ctx: TabContext): boolean {
  const cd = ctx.chartData;
  return !!(
    (cd?.residual_stats && Object.keys(cd.residual_stats).length > 0) ||
    ctx.experimentHistory.some((r) => r.residual_stats)
  );
}

function hasCoefficients(ctx: TabContext): boolean {
  return !!(
    ctx.chartData?.coefficients?.length ||
    ctx.experimentHistory.some((r) => r.coefficients?.length)
  );
}

function hasLearningCurve(ctx: TabContext): boolean {
  return !!(
    ctx.chartData?.learning_curve?.length ||
    ctx.experimentHistory.some((r) => r.learning_curve?.length)
  );
}

function hasForecastData(ctx: TabContext): boolean {
  return !!(
    ctx.chartData?.forecast_data?.length ||
    ctx.experimentHistory.some((r) => r.forecast_data?.length)
  );
}

function hasTrialHistory(ctx: TabContext): boolean {
  return !!(
    ctx.chartData?.trial_history?.length ||
    ctx.experimentHistory.some((r) => r.trial_history?.length)
  );
}

function hasEstimatorComparison(ctx: TabContext): boolean {
  return !!(
    ctx.chartData?.estimator_comparison?.length ||
    ctx.experimentHistory.some((r) => r.estimator_comparison?.length)
  );
}

function hasDataProfile(ctx: TabContext): boolean {
  return ctx.result?.data_profile != null;
}

// ---------------------------------------------------------------------------
// Tab definitions by group
// ---------------------------------------------------------------------------

const COMMON_TABS: TabDefinition[] = [
  {
    id: "overview",
    label: "Overview",
    component: OverviewTabAdapter,
    isAvailable: () => true,
    order: 0,
  },
  {
    id: "experiments",
    label: "Experiments",
    component: ExperimentsTab,
    isAvailable: () => true,
    order: 1,
  },
  {
    id: "plan",
    label: "Plan",
    component: PlanTabAdapter,
    isAvailable: () => true,
    order: 80,
  },
  {
    id: "analysis",
    label: "Analysis",
    component: AnalysisTabAdapter,
    isAvailable: () => true,
    order: 81,
  },
  {
    id: "summary",
    label: "Summary",
    component: SummaryTabAdapter,
    isAvailable: () => true,
    order: 82,
  },
  {
    id: "code",
    label: "Code",
    component: CodeTab,
    isAvailable: () => true,
    order: 83,
  },
  {
    id: "data",
    label: "Data",
    component: DataTab,
    isAvailable: hasDataProfile,
    order: 84,
  },
  {
    id: "journal",
    label: "Journal",
    component: JournalTab,
    isAvailable: () => true,
    order: 85,
  },
];

const CLASSIFICATION_TABS: TabDefinition[] = [
  {
    id: "confusion",
    label: "Confusion Matrix",
    component: ConfusionMatrixTabWrapper,
    isAvailable: hasConfusionMatrix,
    order: 10,
  },
  {
    id: "cv-stability",
    label: "CV Stability",
    component: CVStabilityTabWrapper,
    isAvailable: hasCVFolds,
    order: 11,
  },
  {
    id: "overfit",
    label: "Overfitting",
    component: OverfitTabWrapper,
    isAvailable: () => true,
    order: 12,
  },
  {
    id: "features",
    label: "Features",
    component: FeatureTabWrapper,
    isAvailable: hasFeatureImportance,
    order: 13,
  },
  {
    id: "hyperparams",
    label: "Hyperparams",
    component: HyperparamTabWrapper,
    isAvailable: hasHyperparamSearch,
    order: 14,
  },
  {
    id: "trial-history",
    label: "Trial History",
    component: TrialHistoryTab,
    isAvailable: hasTrialHistory,
    order: 15,
  },
  {
    id: "estimator-comparison",
    label: "Estimators",
    component: EstimatorComparisonTab,
    isAvailable: hasEstimatorComparison,
    order: 16,
  },
];

const REGRESSION_TABS: TabDefinition[] = [
  {
    id: "actual-vs-predicted",
    label: "Predicted vs Actual",
    component: ActualVsPredictedTab,
    isAvailable: hasActualVsPredicted,
    order: 10,
  },
  {
    id: "residuals",
    label: "Residuals",
    component: ResidualPlotTab,
    isAvailable: hasResidualStats,
    order: 11,
  },
  {
    id: "coefficients",
    label: "Coefficients",
    component: CoefficientTab,
    isAvailable: hasCoefficients,
    order: 12,
  },
  {
    id: "learning-curve",
    label: "Learning Curve",
    component: LearningCurveTab,
    isAvailable: hasLearningCurve,
    order: 13,
  },
  {
    id: "cv-stability",
    label: "CV Stability",
    component: CVStabilityTabWrapper,
    isAvailable: hasCVFolds,
    order: 14,
  },
  {
    id: "overfit",
    label: "Overfitting",
    component: OverfitTabWrapper,
    isAvailable: () => true,
    order: 15,
  },
  {
    id: "features",
    label: "Features",
    component: FeatureTabWrapper,
    isAvailable: hasFeatureImportance,
    order: 16,
  },
  {
    id: "hyperparams",
    label: "Hyperparams",
    component: HyperparamTabWrapper,
    isAvailable: hasHyperparamSearch,
    order: 17,
  },
  {
    id: "trial-history",
    label: "Trial History",
    component: TrialHistoryTab,
    isAvailable: hasTrialHistory,
    order: 18,
  },
  {
    id: "estimator-comparison",
    label: "Estimators",
    component: EstimatorComparisonTab,
    isAvailable: hasEstimatorComparison,
    order: 19,
  },
];

const CLUSTERING_TABS: TabDefinition[] = [
  {
    id: "cluster-scatter",
    label: "Clusters",
    component: ClusterScatterTab,
    isAvailable: hasClusterScatter,
    order: 10,
  },
  {
    id: "elbow-curve",
    label: "Elbow Curve",
    component: ElbowCurveTab,
    isAvailable: hasElbowData,
    order: 11,
  },
  {
    id: "silhouette",
    label: "Silhouette",
    component: SilhouetteTab,
    isAvailable: hasSilhouetteData,
    order: 12,
  },
  {
    id: "cluster-profiles",
    label: "Cluster Profiles",
    component: ClusterProfileTab,
    isAvailable: hasClusterProfiles,
    order: 13,
  },
];

const TS_FORECAST_TABS: TabDefinition[] = [
  {
    id: "forecast",
    label: "Forecast",
    component: ForecastPlotTab,
    isAvailable: hasForecastData,
    order: 10,
  },
  {
    id: "trial-history",
    label: "Trial History",
    component: TrialHistoryTab,
    isAvailable: hasTrialHistory,
    order: 11,
  },
  {
    id: "estimator-comparison",
    label: "Estimators",
    component: EstimatorComparisonTab,
    isAvailable: hasEstimatorComparison,
    order: 12,
  },
  {
    id: "features",
    label: "Features",
    component: FeatureTabWrapper,
    isAvailable: hasFeatureImportance,
    order: 13,
  },
  {
    id: "overfit",
    label: "Overfitting",
    component: OverfitTabWrapper,
    isAvailable: () => true,
    order: 14,
  },
];

const TASK_TYPE_TABS: Record<string, TabDefinition[]> = {
  classification: CLASSIFICATION_TABS,
  regression: REGRESSION_TABS,
  clustering: CLUSTERING_TABS,
  ts_forecast: TS_FORECAST_TABS,
};

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Get the list of available tabs for a given result context.
 * Merges common tabs with task-specific tabs, filters by data availability,
 * and sorts by order.
 */
export function getTabsForResult(
  problemType: string | null | undefined,
  ctx: TabContext,
): TabDefinition[] {
  const taskTabs = TASK_TYPE_TABS[problemType ?? "classification"] ?? CLASSIFICATION_TABS;
  const allTabs = [...COMMON_TABS, ...taskTabs];
  return allTabs.filter((tab) => tab.isAvailable(ctx)).sort((a, b) => a.order - b.order);
}
