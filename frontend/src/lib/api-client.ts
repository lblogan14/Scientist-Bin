import ky from "ky";
import type {
  Experiment,
  HealthResponse,
  TrainRequest,
} from "@/types/api";

const api = ky.create({
  prefixUrl: "/api/v1",
  timeout: 30_000,
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

export async function checkHealth(): Promise<HealthResponse> {
  return api.get("health").json<HealthResponse>();
}
