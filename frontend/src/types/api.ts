export type ExperimentStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed";

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
  | "execution"
  | "analysis"
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
  | "experiment_done";

// ---------------------------------------------------------------------------
// Request types
// ---------------------------------------------------------------------------

export interface TrainRequest {
  objective: string;
  data_description?: string;
  data_file_path?: string;
  framework_preference?: Framework;
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
  created_at: string;
  updated_at: string;
}

export interface Run {
  id: string;
  experiment_id: string;
  algorithm: string;
  hyperparameters: Record<string, unknown>;
  metrics: MetricPoint[];
  final_metrics: Record<string, number> | null;
  status: string;
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

// ---------------------------------------------------------------------------
// Result types (from completed experiments)
// ---------------------------------------------------------------------------

export interface ExperimentResult {
  framework: string;
  plan: Record<string, unknown> | null;
  generated_code: string | null;
  evaluation_results: Record<string, unknown> | null;
  experiment_history: ExperimentRecord[];
  data_profile: DataProfile | null;
  problem_type: string | null;
  iterations: number;
  status: string;
}

export interface ExperimentRecord {
  iteration: number;
  algorithm: string;
  hyperparameters: Record<string, unknown>;
  metrics: Record<string, number>;
  training_time_seconds: number;
  timestamp: string;
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
