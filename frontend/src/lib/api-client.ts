import ky from "ky";
import type {
  Experiment,
  HealthResponse,
  JournalEntry,
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
