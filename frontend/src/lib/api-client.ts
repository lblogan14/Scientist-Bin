import ky from "ky";
import type {
  ArtifactType,
  ExecutionPlan,
  Experiment,
  HealthResponse,
  JournalEntry,
  PaginatedExperiments,
  ReviewRequest,
  TrainRequest,
} from "@/types/api";

const api = ky.create({
  prefixUrl: "/api/v1",
  timeout: 120_000,
});

/**
 * Extract a human-readable error message from a ky HTTPError or generic Error.
 */
export async function extractErrorMessage(error: unknown): Promise<string> {
  if (
    error &&
    typeof error === "object" &&
    "response" in error &&
    error.response instanceof Response
  ) {
    try {
      const body = await error.response.json();
      if (body.detail) return String(body.detail);
    } catch {
      // Response body not JSON
    }
    return `Request failed (${error.response.status})`;
  }
  if (error instanceof Error) return error.message;
  return "An unexpected error occurred";
}

export async function submitTrainRequest(
  request: TrainRequest,
): Promise<Experiment> {
  return api.post("train", { json: request }).json<Experiment>();
}

export interface ListExperimentsParams {
  status?: string;
  framework?: string;
  search?: string;
  offset?: number;
  limit?: number;
}

export async function listExperiments(
  params?: ListExperimentsParams,
): Promise<PaginatedExperiments> {
  const searchParams: Record<string, string> = {};
  if (params?.status) searchParams.status = params.status;
  if (params?.framework) searchParams.framework = params.framework;
  if (params?.search) searchParams.search = params.search;
  if (params?.offset !== undefined) searchParams.offset = String(params.offset);
  if (params?.limit !== undefined) searchParams.limit = String(params.limit);

  return api.get("experiments", { searchParams }).json<PaginatedExperiments>();
}

export async function getExperiment(id: string): Promise<Experiment> {
  return api.get(`experiments/${id}`).json<Experiment>();
}

export async function deleteExperiment(id: string): Promise<void> {
  await api.delete(`experiments/${id}`);
}

export async function getExperimentJournal(
  id: string,
): Promise<JournalEntry[]> {
  return api.get(`experiments/${id}/journal`).json<JournalEntry[]>();
}

export async function submitPlanReview(
  id: string,
  review: ReviewRequest,
): Promise<{ status: string }> {
  return api.post(`experiments/${id}/review`, { json: review }).json();
}

export async function getExperimentPlan(
  id: string,
): Promise<{ execution_plan: ExecutionPlan | null }> {
  return api.get(`experiments/${id}/plan`).json();
}

export async function getExperimentAnalysis(
  id: string,
): Promise<{ analysis_report: string | null; split_data_paths: Record<string, string> | null }> {
  return api.get(`experiments/${id}/analysis`).json();
}

export async function getExperimentSummary(
  id: string,
): Promise<{ summary_report: string | null }> {
  return api.get(`experiments/${id}/summary`).json();
}

export async function checkHealth(): Promise<HealthResponse> {
  return api.get("health").json<HealthResponse>();
}

/**
 * Create an SSE connection for real-time experiment events.
 * Returns an EventSource that emits typed events.
 */
export function createExperimentEventSource(experimentId: string): EventSource {
  return new EventSource(`/api/v1/experiments/${experimentId}/events`);
}

export function getArtifactDownloadUrl(
  experimentId: string,
  artifactType: ArtifactType,
): string {
  return `/api/v1/experiments/${experimentId}/artifacts/${artifactType}`;
}

export function getModelDownloadUrl(experimentId: string): string {
  return getArtifactDownloadUrl(experimentId, "model");
}

export function getResultsDownloadUrl(experimentId: string): string {
  return getArtifactDownloadUrl(experimentId, "results");
}
