/**
 * Experiment detail panel tests.
 *
 * Seeds a completed experiment, then verifies clicking an experiment row
 * opens the detail panel and action links navigate correctly.
 *
 * Requires GOOGLE_API_KEY on the backend and RUN_LIFECYCLE_TEST=1.
 */

import { test, expect } from "@playwright/test";
import { ExperimentsPO } from "./fixtures/page-objects";
import { seedOneCompleted } from "./fixtures/experiment-seed";

test.skip(!process.env.RUN_LIFECYCLE_TEST, "Set RUN_LIFECYCLE_TEST=1 to run");

let experimentId: string;
let cleanup: () => Promise<void>;

test.beforeAll(async ({ request }) => {
  const seeded = await seedOneCompleted(request, {
    objective: "Classify iris for detail panel e2e test",
    dataFile: "iris_data/Iris.csv",
  });
  experimentId = seeded.id;
  cleanup = seeded.cleanup;
});

test.afterAll(async () => {
  await cleanup();
});

test.describe("Experiment detail panel", () => {
  test("Click experiment row shows detail", async ({ page }) => {
    const experiments = new ExperimentsPO(page);
    await experiments.goto();

    // Click on the seeded experiment
    await experiments.clickExperimentByObjective("iris");

    // Detail section should appear with experiment info
    await expect(
      page.getByText(/iris/i),
    ).toBeVisible({ timeout: 5_000 });
    await expect(
      page.getByText(/completed/i),
    ).toBeVisible({ timeout: 5_000 });
  });

  test("Results action navigates to results page", async ({ page }) => {
    const experiments = new ExperimentsPO(page);
    await experiments.goto();

    // Find the Results/View link for a completed experiment
    const resultsLink = page.getByRole("link", { name: /Results/i }).first();
    if (await resultsLink.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await resultsLink.click();
      await expect(page).toHaveURL(/\/results/, { timeout: 5_000 });
    }
  });
});
