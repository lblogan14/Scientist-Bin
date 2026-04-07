/**
 * Experiment list filtering and search tests.
 *
 * Seeds completed experiments, then verifies status/framework/problem-type
 * filters, text search, combined filters, and count accuracy.
 *
 * Requires GOOGLE_API_KEY on the backend and RUN_LIFECYCLE_TEST=1.
 */

import { test, expect } from "@playwright/test";
import { ExperimentsPO } from "./fixtures/page-objects";
import { seedCompletedExperiments } from "./fixtures/experiment-seed";

test.skip(!process.env.RUN_LIFECYCLE_TEST, "Set RUN_LIFECYCLE_TEST=1 to run");

let classificationId: string;
let regressionId: string;
let cleanup: () => Promise<void>;

test.beforeAll(async ({ request }) => {
  const seeded = await seedCompletedExperiments(request);
  classificationId = seeded.classificationId;
  regressionId = seeded.regressionId;
  cleanup = seeded.cleanup;
});

test.afterAll(async () => {
  await cleanup();
});

test.describe("Experiment filtering", () => {
  test("Status filter shows only completed experiments", async ({ page }) => {
    const experiments = new ExperimentsPO(page);
    await experiments.goto();

    await experiments.filterByStatus("Completed");

    // All visible rows should show "completed" badge
    const rows = page.locator("tbody tr").filter({
      hasNot: page.locator("text=No experiments"),
    });
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);

    for (let i = 0; i < count; i++) {
      const rowText = await rows.nth(i).textContent();
      expect(rowText?.toLowerCase()).toContain("completed");
    }
  });

  test("Framework filter shows only sklearn experiments", async ({ page }) => {
    const experiments = new ExperimentsPO(page);
    await experiments.goto();

    await experiments.filterByFramework("Scikit-learn");

    const rows = page.locator("tbody tr").filter({
      hasNot: page.locator("text=No experiments"),
    });
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);

    for (let i = 0; i < count; i++) {
      const rowText = await rows.nth(i).textContent();
      expect(rowText?.toLowerCase()).toMatch(/sklearn|scikit/);
    }
  });

  test("Search by objective text", async ({ page }) => {
    const experiments = new ExperimentsPO(page);
    await experiments.goto();

    await experiments.searchExperiments("iris");

    const rows = page.locator("tbody tr").filter({
      hasNot: page.locator("text=No experiments"),
    });
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);

    for (let i = 0; i < count; i++) {
      const rowText = await rows.nth(i).textContent();
      expect(rowText?.toLowerCase()).toContain("iris");
    }
  });

  test("Combined filters narrow results", async ({ page }) => {
    const experiments = new ExperimentsPO(page);
    await experiments.goto();

    await experiments.filterByStatus("Completed");
    await experiments.filterByFramework("Scikit-learn");

    const rows = page.locator("tbody tr").filter({
      hasNot: page.locator("text=No experiments"),
    });
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test("Showing count is accurate", async ({ page }) => {
    const experiments = new ExperimentsPO(page);
    await experiments.goto();

    // Wait for experiments to load
    await page.waitForTimeout(1_000);

    const { showing, total } = await experiments.getShowingCount();
    if (total > 0) {
      const visibleCount = await experiments.getVisibleRowCount();
      expect(showing).toBe(visibleCount);
      expect(showing).toBeLessThanOrEqual(total);
    }
  });

  test("Clear search resets results", async ({ page }) => {
    const experiments = new ExperimentsPO(page);
    await experiments.goto();

    // Get initial count
    await page.waitForTimeout(1_000);
    const initial = await experiments.getShowingCount();

    // Apply search filter
    await experiments.searchExperiments("iris");
    await page.waitForTimeout(500);
    const filtered = await experiments.getShowingCount();
    expect(filtered.showing).toBeLessThanOrEqual(initial.showing);

    // Clear search
    await experiments.clearSearch();
    await page.waitForTimeout(500);
    const cleared = await experiments.getShowingCount();
    expect(cleared.showing).toBe(initial.showing);
  });
});
