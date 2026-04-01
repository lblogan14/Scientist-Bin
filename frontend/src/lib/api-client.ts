import ky from "ky";
import type {
  Experiment,
  HealthResponse,
  JournalEntry,
  ReviewRequest,
  TrainRequest,
} from "@/types/api";

const api = ky.create({
  prefixUrl: "/api/v1",
  timeout: 120_000,
});

export async function submitTrainRequest(
  request: TrainRequest,
): Promise<Experiment> {
  return api.post("train", { json: request }).json<Experiment>();
}

export async function listExperiments(): Promise<Experiment[]> {
  return api.get("experiments").json<Experiment[]>();
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

export async function getExperimentPlan(
  id: string,
): Promise<{ execution_plan: Record<string, unknown> | null }> {
  return api.get(`experiments/${id}/plan`).json();
}

export async function getExperimentAnalysis(
  id: string,
): Promise<{
  analysis_report: string | null;
  split_data_paths: Record<string, string> | null;
}> {
  return api.get(`experiments/${id}/analysis`).json();
}

export async function getExperimentSummary(
  id: string,
): Promise<{ summary_report: string | null }> {
  return api.get(`experiments/${id}/summary`).json();
}

export async function submitPlanReview(
  id: string,
  review: ReviewRequest,
): Promise<{ status: string }> {
  return api.post(`experiments/${id}/review`, { json: review }).json();
}

export async function checkHealth(): Promise<HealthResponse> {
  return api.get("health").json<HealthResponse>();
}

/**
 * Create an SSE connection for real-time experiment events.
 * Returns an EventSource that emits typed events.
 */
export function createExperimentEventSource(
  experimentId: string,
): EventSource {
  return new EventSource(`/api/v1/experiments/${experimentId}/events`);
}

export function getModelDownloadUrl(experimentId: string): string {
  return `/api/v1/experiments/${experimentId}/artifacts/model`;
}

export function getResultsDownloadUrl(experimentId: string): string {
  return `/api/v1/experiments/${experimentId}/artifacts/results`;
}
