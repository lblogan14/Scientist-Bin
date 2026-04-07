/**
 * API helper for seeding and managing experiments in E2E tests.
 *
 * Uses Playwright's APIRequestContext to call the backend directly
 * (bypassing the Vite proxy), which is useful for setup/teardown.
 */

import type { APIRequestContext } from "@playwright/test";

const API_BASE = "http://localhost:8000/api/v1";

interface CreateExperimentOpts {
  objective: string;
  data_file_path?: string;
  framework_preference?: string;
  auto_approve_plan?: boolean;
  data_description?: string;
}

interface Experiment {
  id: string;
  status: string;
  framework: string | null;
  problem_type: string | null;
  result: unknown;
  [key: string]: unknown;
}

export async function createExperiment(
  request: APIRequestContext,
  opts: CreateExperimentOpts,
): Promise<Experiment> {
  const response = await request.post(`${API_BASE}/train`, { data: opts });
  if (!response.ok()) {
    throw new Error(
      `Failed to create experiment: ${response.status()} ${await response.text()}`,
    );
  }
  return response.json();
}

export async function getExperiment(
  request: APIRequestContext,
  id: string,
): Promise<Experiment> {
  const response = await request.get(`${API_BASE}/experiments/${id}`);
  if (!response.ok()) {
    throw new Error(`Failed to get experiment ${id}: ${response.status()}`);
  }
  return response.json();
}

export async function deleteExperiment(
  request: APIRequestContext,
  id: string,
): Promise<void> {
  await request.delete(`${API_BASE}/experiments/${id}`);
}

export async function waitForComplete(
  request: APIRequestContext,
  id: string,
  timeoutMs = 300_000,
  pollIntervalMs = 5_000,
): Promise<Experiment> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const exp = await getExperiment(request, id);
    if (exp.status === "completed" || exp.status === "failed") {
      return exp;
    }
    await new Promise((r) => setTimeout(r, pollIntervalMs));
  }
  throw new Error(
    `Experiment ${id} did not complete within ${timeoutMs / 1000}s`,
  );
}

export async function checkHealth(
  request: APIRequestContext,
): Promise<{ status: string; frameworks: Record<string, string> }> {
  const response = await request.get(`${API_BASE}/health`);
  return response.json();
}
