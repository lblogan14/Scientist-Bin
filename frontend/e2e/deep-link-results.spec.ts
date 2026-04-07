/**
 * Deep-link results page tests.
 *
 * Verifies that navigating directly to /results/:id and /results?id=
 * loads the correct experiment results with tabs and metrics.
 *
 * Requires GOOGLE_API_KEY on the backend and RUN_LIFECYCLE_TEST=1.
 */

import { test, expect } from "@playwright/test";
import { ResultsPO } from "./fixtures/page-objects";
import { seedOneCompleted } from "./fixtures/experiment-seed";
import {
  extractMetricCardValues,
  collectConsoleErrors,
} from "./fixtures/chart-helpers";

test.skip(!process.env.RUN_LIFECYCLE_TEST, "Set RUN_LIFECYCLE_TEST=1 to run");

let experimentId: string;
let cleanup: () => Promise<void>;

test.beforeAll(async ({ request }) => {
  const seeded = await seedOneCompleted(request, {
    objective: "Classify iris for deep-link e2e test",
    dataFile: "iris_data/Iris.csv",
  });
  experimentId = seeded.id;
  cleanup = seeded.cleanup;
});

test.afterAll(async () => {
  await cleanup();
});

test.describe("Deep-link results", () => {
  test("Navigate to /results/:id loads correct experiment", async ({ page }) => {
    await page.goto(`/results/${experimentId}`);

    await expect(
      page.getByRole("heading", { name: /Results/i }),
    ).toBeVisible({ timeout: 15_000 });

    // Metric cards should render
    const metrics = await extractMetricCardValues(page);
    expect(Object.keys(metrics).length).toBeGreaterThan(0);

    // Overview tab should be active
    const results = new ResultsPO(page);
    await results.verifyTabsPresent(["Overview", "Experiments"]);
  });

  test("Navigate to /results?id= loads correct experiment", async ({ page }) => {
    await page.goto(`/results?id=${experimentId}`);

    await expect(
      page.getByRole("heading", { name: /Results/i }),
    ).toBeVisible({ timeout: 15_000 });

    // Metric cards should render
    const metrics = await extractMetricCardValues(page);
    expect(Object.keys(metrics).length).toBeGreaterThan(0);
  });

  test("Tabs render correctly on deep-linked results", async ({ page }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto(`/results?id=${experimentId}`);
    await expect(
      page.getByRole("heading", { name: /Results/i }),
    ).toBeVisible({ timeout: 15_000 });

    const results = new ResultsPO(page);

    // Click through all visible tabs
    const visibleTabs = await results.getVisibleTabs();
    expect(visibleTabs.length).toBeGreaterThan(0);

    for (const tabName of visibleTabs) {
      await results.clickTab(tabName);
      await results.waitForTabContent();
    }

    // No console errors during tab switching
    expect(
      consoleErrors,
      `Console errors during tab switching: ${consoleErrors.join("; ")}`,
    ).toHaveLength(0);
  });
});
