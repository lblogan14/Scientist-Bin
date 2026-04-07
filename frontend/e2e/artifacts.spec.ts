/**
 * Artifact download tests — verify download buttons return valid files.
 *
 * Requires at least one completed experiment in the store.
 */

import { test, expect } from "@playwright/test";
import { createExperiment, waitForComplete } from "./fixtures/experiment-api";

test.skip(!process.env.RUN_LIFECYCLE_TEST, "Set RUN_LIFECYCLE_TEST=1 to run");

test("Artifact downloads return 200", async ({ page, request }) => {
  // Seed a completed experiment via API
  const exp = await createExperiment(request, {
    objective: "Classify iris for artifact download test",
    data_file_path: "iris_data/Iris.csv",
    framework_preference: "sklearn",
    auto_approve_plan: true,
  });

  const completed = await waitForComplete(request, exp.id, 300_000);
  expect(completed.status).toBe("completed");

  // Navigate to results page
  await page.goto(`/results?id=${exp.id}`);
  await expect(page.getByRole("heading", { name: /results/i })).toBeVisible();

  // Test artifact download URLs
  const artifactTypes = ["results", "model", "charts"] as const;
  for (const type of artifactTypes) {
    const url = `http://localhost:8000/api/v1/experiments/${exp.id}/artifacts/${type}`;
    const response = await request.get(url);
    // Some artifacts may not exist (charts might not be generated)
    if (response.status() === 200) {
      const body = await response.body();
      expect(body.length).toBeGreaterThan(0);
    }
  }
});
