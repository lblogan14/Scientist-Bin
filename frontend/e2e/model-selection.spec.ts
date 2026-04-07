/**
 * Model selection page tests.
 *
 * Requires at least one completed experiment.
 */

import { test, expect } from "@playwright/test";
import { createExperiment, waitForComplete } from "./fixtures/experiment-api";

test.skip(!process.env.RUN_LIFECYCLE_TEST, "Set RUN_LIFECYCLE_TEST=1 to run");

test("Models page shows ranking after completed experiment", async ({ page, request }) => {
  // Seed a completed experiment
  const exp = await createExperiment(request, {
    objective: "Classify iris for model selection test",
    data_file_path: "iris_data/Iris.csv",
    framework_preference: "sklearn",
    auto_approve_plan: true,
  });

  await waitForComplete(request, exp.id, 300_000);

  // Navigate to models page
  await page.goto("/models");
  await expect(
    page.getByRole("heading", { name: "Models", exact: true }),
  ).toBeVisible();

  // Should show at least one model card
  await expect(page.locator("[class*='card']").first()).toBeVisible({
    timeout: 10_000,
  });
});
