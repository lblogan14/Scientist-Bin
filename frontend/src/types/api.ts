export type ExperimentStatus = "pending" | "running" | "completed" | "failed";

export type Framework =
  | "sklearn"
  | "pytorch"
  | "tensorflow"
  | "transformers"
  | "diffusers";

export type ExperimentPhase =
  | "initializing"
  | "classify"
  | "eda"
  | "planning"
  | "plan_review"
  | "data_analysis"
  | "execution"
  | "analysis"
  | "summarizing"
  | "done"
  | "error";

export type ProgressEventType =
  | "phase_change"
  | "metric_update"
  | "agent_activity"
  | "log_output"
  | "run_started"
  | "run_completed"
  | "error"
  | "experiment_done"
  | "plan_review_pending"
  | "plan_review_submitted"
  | "plan_completed"
  | "analysis_completed"
  | "framework_completed"
  | "summary_completed";

export type RunStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "timeout";

export type ArtifactType =
  | "model"
  | "results"
  | "analysis"
  | "summary"
  | "plan"
  | "charts"
  | "journal";

// ---------------------------------------------------------------------------
// Request types
// ---------------------------------------------------------------------------

export interface TrainRequest {
  objective: string;
  data_description?: string;
  data_file_path?: string;
  framework_preference?: Framework;
  auto_approve_plan?: boolean;
  deep_research?: boolean;
  budget_max_iterations?: number;
  budget_time_limit_seconds?: number;
}

export interface ReviewRequest {
  feedback: string;
}

// ---------------------------------------------------------------------------
// Core experiment types
// ---------------------------------------------------------------------------

export interface Experiment {
  id: string;
  objective: string;
  data_description: string;
  data_file_path: string | null;
  framework: Framework | null;
  status: ExperimentStatus;
  phase: ExperimentPhase | null;
  runs: Run[];
  best_run_id: string | null;
  iteration_count: number;
  progress_events: ProgressEvent[];
  result: ExperimentResult | ExperimentError | null;
  execution_plan: Record<string, unknown> | null;
  analysis_report: string | null;
  summary_report: string | null;
  split_data_paths: Record<string, string> | null;
  problem_type: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedExperiments {
  experiments: Experiment[];
  total: number;
  offset: number;
  limit: number;
}

export interface Run {
  id: string;
  experiment_id: string;
  algorithm: string;
  hyperparameters: Record<string, unknown>;
  metrics: MetricPoint[];
  final_metrics: Record<string, number> | null;
  status: RunStatus;
  code: string;
  stdout: string;
  stderr: string;
  started_at: string | null;
  completed_at: string | null;
  wall_time_seconds: number | null;
  artifacts: string[];
}

export interface MetricPoint {
  name: string;
  value: number;
  step: number | null;
  timestamp: string;
}

export interface ProgressEvent {
  event_type: ProgressEventType;
  timestamp: string;
  data: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Error types (from failed experiments)
// ---------------------------------------------------------------------------

export interface ExperimentError {
  error: string;
  traceback?: string;
}

export function isExperimentError(
  result: ExperimentResult | ExperimentError | null,
): result is ExperimentError {
  return result !== null && "error" in result;
}

export function isExperimentResult(
  result: ExperimentResult | ExperimentError | null,
): result is ExperimentResult {
  return result !== null && !isExperimentError(result);
}

// ---------------------------------------------------------------------------
// Result types (from completed experiments)
// ---------------------------------------------------------------------------

export interface ExecutionPlan {
  approach_summary: string;
  problem_type: string;
  target_column: string | null;
  algorithms_to_try: string[];
  pipeline_preprocessing_steps: string[];
  feature_engineering_steps: string[];
  evaluation_metrics: string[];
  cv_strategy: string;
  success_criteria: Record<string, number>;
  hyperparameter_tuning_approach: string;
}

export interface ChartData {
  model_comparison?: Array<Record<string, unknown>>;
  cv_fold_scores?: Record<
    string,
    Record<string, { scores: number[]; mean: number }>
  >;
  feature_importances?: { algorithm: string; features: FeatureImportance[] };
  confusion_matrices?: Record<string, ConfusionMatrix>;
  training_times?: Array<{ algorithm: string; time_seconds: number }>;
  hyperparam_search?: Record<string, CVResultEntry[]>;
  residual_stats?: Record<string, ResidualStats>;
  // Clustering additions
  cluster_scatter?: ClusterScatterPoint[];
  elbow_curve?: ElbowPoint[];
  cluster_profiles?: ClusterProfile[];
  silhouette_data?: SilhouetteSample[];
  // Regression additions
  actual_vs_predicted?: ActualVsPredictedPoint[];
  coefficients?: CoefficientEntry[];
  learning_curve?: LearningCurvePoint[];
}

export interface SummaryReportSections {
  title: string;
  executive_summary: string;
  dataset_overview: string;
  methodology: string;
  model_comparison_table: string;
  cv_stability_analysis: string;
  best_model_analysis: string;
  feature_importance_analysis: string;
  hyperparameter_analysis: string;
  error_analysis: string;
  conclusions: string;
  recommendations: string[];
  reproducibility_notes: string;
  chart_data?: ChartData;
}

export interface OverfitEntry {
  algorithm: string;
  metric_name: string;
  train_value: number;
  val_value: number;
  gap: number;
  gap_percentage: number;
  overfit_risk: "low" | "moderate" | "high";
}

export interface ExperimentResult {
  framework: string;
  plan: Record<string, unknown> | null;
  plan_markdown: string | null;
  generated_code: string | null;
  evaluation_results: Record<string, unknown> | null;
  experiment_history: ExperimentRecord[];
  data_profile: DataProfile | null;
  problem_type: string | null;
  iterations: number;
  analysis_report: string | null;
  summary_report: string | null;
  best_model: string | null;
  best_hyperparameters: Record<string, unknown> | null;
  test_metrics: Record<string, number> | null;
  test_diagnostics: Record<string, unknown> | null;
  selection_reasoning: string | null;
  report_sections: SummaryReportSections | null;
  status: string;
}

export interface CVResultEntry {
  params: Record<string, unknown>;
  mean_score: number;
  std_score: number;
  rank: number;
}

export interface FeatureImportance {
  feature: string;
  importance: number;
}

export interface ConfusionMatrix {
  labels: string[];
  matrix: number[][];
}

export interface ResidualStats {
  mean_residual: number;
  std_residual: number;
  max_abs_residual: number;
  residual_percentiles: Record<string, number>;
}

// ---------------------------------------------------------------------------
// Clustering-specific chart data
// ---------------------------------------------------------------------------

export interface ClusterScatterPoint {
  x: number;
  y: number;
  cluster: number;
}

export interface ElbowPoint {
  k: number;
  inertia: number;
}

export interface ClusterProfile {
  cluster_id: number;
  size: number;
  centroid: Record<string, number>;
}

export interface SilhouetteSample {
  sample_index: number;
  score: number;
  cluster: number;
}

// ---------------------------------------------------------------------------
// Regression-specific chart data
// ---------------------------------------------------------------------------

export interface ActualVsPredictedPoint {
  actual: number;
  predicted: number;
}

export interface CoefficientEntry {
  feature: string;
  coefficient: number;
}

export interface LearningCurvePoint {
  train_size: number;
  train_score: number;
  val_score: number;
}

export interface ExperimentRecord {
  iteration: number;
  algorithm: string;
  hyperparameters: Record<string, unknown>;
  metrics: Record<string, number>;
  training_time_seconds: number;
  timestamp: string;
  cv_fold_scores?: Record<string, number[]>;
  cv_results_top_n?: CVResultEntry[];
  feature_importances?: FeatureImportance[];
  confusion_matrix?: ConfusionMatrix;
  residual_stats?: ResidualStats;
  // Clustering additions
  cluster_scatter?: ClusterScatterPoint[];
  elbow_data?: ElbowPoint[];
  cluster_sizes?: number[];
  n_clusters?: number;
  silhouette_per_sample?: SilhouetteSample[];
  cluster_profiles?: ClusterProfile[];
  // Regression additions
  actual_vs_predicted?: ActualVsPredictedPoint[];
  coefficients?: CoefficientEntry[];
  learning_curve?: LearningCurvePoint[];
}

export interface DataProfile {
  file_path: string;
  shape: [number, number];
  column_names: string[];
  dtypes: Record<string, string>;
  missing_counts: Record<string, number>;
  numeric_columns: string[];
  categorical_columns: string[];
  target_column: string | null;
  class_distribution: Record<string, number> | null;
  target_stats: Record<string, number> | null;
  statistics_summary: string;
  data_quality_issues: string[];
}

// ---------------------------------------------------------------------------
// Journal types
// ---------------------------------------------------------------------------

export interface JournalEntry {
  timestamp: string;
  event: string;
  phase: string;
  iteration: number | null;
  reasoning: string;
  data: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Agent activity (used in SSE streaming)
// ---------------------------------------------------------------------------

export interface AgentActivity {
  agent: string;
  action: string;
  timestamp: string;
  details?: string;
  data?: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

export interface HealthResponse {
  status: "ok";
}

// ---------------------------------------------------------------------------
// Deployment types
// ---------------------------------------------------------------------------

export type DeploymentStatus =
  | "not_deployed"
  | "deploying"
  | "deployed"
  | "failed"
  | "stopped";

export interface DeploymentInfo {
  status: DeploymentStatus;
  endpoint_url: string | null;
  deployed_at: string | null;
  model_version: string;
}
