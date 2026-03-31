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

export interface TrainRequest {
  objective: string;
  data_description?: string;
  framework_preference?: Framework;
}

export interface Experiment {
  id: string;
  objective: string;
  data_description: string;
  framework: Framework | null;
  status: ExperimentStatus;
  result: ExperimentResult | null;
  created_at: string;
  updated_at: string;
}

export interface ExperimentResult {
  framework: string;
  plan: string | null;
  generated_code: string | null;
  evaluation_results: Record<string, unknown> | null;
  status: string;
}

export interface AgentActivity {
  agent: string;
  action: string;
  timestamp: string;
  details?: string;
}

export interface HealthResponse {
  status: "ok";
}
