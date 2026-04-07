/**
 * Experiment seeding helpers for E2E tests that need pre-existing experiments.
 *
 * Provides utilities to create experiments via the API and wait for
 * specific phases or completion, used in beforeAll/afterAll hooks.
 */

import type { APIRequestContext } from "@playwright/test";
import {
  createExperiment,
  getExperiment,
  deleteExperiment,
  waitForComplete,
} from "./experiment-api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface SeededExperiments {
  classificationId: string;
  regressionId: string;
  cleanup: () => Promise<void>;
}

interface SeededExperiment {
  id: string;
  cleanup: () => Promise<void>;
}

// ---------------------------------------------------------------------------
// Wait for a specific phase
// ---------------------------------------------------------------------------

/**
 * Poll until the experiment reaches a specific phase.
 * Useful for tests that need an experiment in `plan_review` state.
 */
export async function waitForPhase(
  request: APIRequestContext,
  id: string,
  targetPhase: string,
  timeoutMs = 180_000,
  pollIntervalMs = 3_000,
): Promise<Record<string, unknown>> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const exp = await getExperiment(request, id);
    if (exp.phase === targetPhase) return exp as Record<string, unknown>;
    // If experiment already completed or failed, stop waiting
    if (exp.status === "completed" || exp.status === "failed") {
      throw new Error(
        `Experiment ${id} reached status "${exp.status}" before phase "${targetPhase}"`,
      );
    }
    await new Promise((r) => setTimeout(r, pollIntervalMs));
  }
  throw new Error(
    `Experiment ${id} did not reach phase "${targetPhase}" within ${timeoutMs / 1000}s`,
  );
}

// ---------------------------------------------------------------------------
// Seed completed experiments
// ---------------------------------------------------------------------------

/**
 * Seed two completed experiments (classification + regression) for tests
 * that need pre-existing data (filtering, detail panel, downloads, etc.).
 *
 * Call in test.beforeAll, and call cleanup() in test.afterAll.
 */
export async function seedCompletedExperiments(
  request: APIRequestContext,
  timeoutMs = 300_000,
): Promise<SeededExperiments> {
  // Launch both in parallel
  const [classExp, regExp] = await Promise.all([
    createExperiment(request, {
      objective: "Classify iris species for e2e seed test",
      data_file_path: "iris_data/Iris.csv",
      framework_preference: "sklearn",
      auto_approve_plan: true,
    }),
    createExperiment(request, {
      objective: "Predict wine quality for e2e seed test",
      data_file_path: "wine_data/WineQT.csv",
      framework_preference: "sklearn",
      auto_approve_plan: true,
    }),
  ]);

  // Wait for both to complete
  await Promise.all([
    waitForComplete(request, classExp.id, timeoutMs),
    waitForComplete(request, regExp.id, timeoutMs),
  ]);

  return {
    classificationId: classExp.id,
    regressionId: regExp.id,
    cleanup: async () => {
      await deleteExperiment(request, classExp.id).catch(() => {});
      await deleteExperiment(request, regExp.id).catch(() => {});
    },
  };
}

/**
 * Seed a single completed experiment.
 */
export async function seedOneCompleted(
  request: APIRequestContext,
  opts: {
    objective: string;
    dataFile: string;
    framework?: string;
  },
  timeoutMs = 300_000,
): Promise<SeededExperiment> {
  const exp = await createExperiment(request, {
    objective: opts.objective,
    data_file_path: opts.dataFile,
    framework_preference: opts.framework ?? "sklearn",
    auto_approve_plan: true,
  });

  await waitForComplete(request, exp.id, timeoutMs);

  return {
    id: exp.id,
    cleanup: async () => {
      await deleteExperiment(request, exp.id).catch(() => {});
    },
  };
}

/**
 * Seed an experiment that will pause at plan_review phase.
 * Does NOT auto-approve, so the caller must approve or clean up.
 */
export async function seedPlanReviewExperiment(
  request: APIRequestContext,
  opts?: {
    objective?: string;
    dataFile?: string;
    framework?: string;
  },
  phaseTimeoutMs = 180_000,
): Promise<SeededExperiment> {
  const exp = await createExperiment(request, {
    objective:
      opts?.objective ?? "Classify iris for plan review e2e test",
    data_file_path: opts?.dataFile ?? "iris_data/Iris.csv",
    framework_preference: opts?.framework ?? "sklearn",
    auto_approve_plan: false, // Will pause at plan_review
  });

  // Wait for it to reach plan_review
  await waitForPhase(request, exp.id, "plan_review", phaseTimeoutMs);

  return {
    id: exp.id,
    cleanup: async () => {
      await deleteExperiment(request, exp.id).catch(() => {});
    },
  };
}
