/**
 * Page refresh mid-training tests.
 *
 * Verifies that refreshing the browser during training reconnects SSE
 * and that refreshing the results page preserves data.
 *
 * Requires GOOGLE_API_KEY on the backend and RUN_LIFECYCLE_TEST=1.
 */

import { test, expect } from "@playwright/test";
import { DashboardPO, MonitorPO, ResultsPO } from "./fixtures/page-objects";
import { extractMetricCardValues } from "./fixtures/chart-helpers";

test.skip(!process.env.RUN_LIFECYCLE_TEST, "Set RUN_LIFECYCLE_TEST=1 to run");

test("Page refresh during training reconnects SSE", async ({ page }) => {
  const dashboard = new DashboardPO(page);
  await dashboard.goto();
  await dashboard.fillAndSubmit(
    "Classify iris for page refresh e2e test",
    "iris_data/Iris.csv",
    { framework: "sklearn", autoApprove: true },
  );

  await expect(page).toHaveURL(/\/monitor\?id=/, { timeout: 10_000 });

  // Wait a moment for SSE to connect and some events to arrive
  await page.waitForTimeout(5_000);

  // Refresh the page mid-training
  await page.reload();

  // After refresh, the monitor page should re-render
  await expect(
    page.getByRole("heading", { name: /Training/i }),
  ).toBeVisible({ timeout: 10_000 });

  // SSE should reconnect — either "Live" indicator or phase progress should appear
  await expect(
    page.getByText(/Live/).or(
      page.getByText(/initializing|classify|eda|planning|execution|analysis|summarizing|done/i),
    ),
  ).toBeVisible({ timeout: 15_000 });

  // Wait for training to complete
  const monitor = new MonitorPO(page);
  await monitor.waitForCompletion(300_000);
});

test("Page refresh on results page preserves data", async ({ page }) => {
  // Start a training and wait for completion
  const dashboard = new DashboardPO(page);
  await dashboard.goto();
  await dashboard.fillAndSubmit(
    "Classify iris for results refresh e2e test",
    "iris_data/Iris.csv",
    { framework: "sklearn", autoApprove: true },
  );

  await expect(page).toHaveURL(/\/monitor\?id=/, { timeout: 10_000 });
  const monitor = new MonitorPO(page);
  await monitor.waitForCompletion(300_000);

  // Now on results page — verify metrics are present
  const results = new ResultsPO(page);
  const metricsBefore = await extractMetricCardValues(page);
  expect(Object.keys(metricsBefore).length).toBeGreaterThan(0);

  // Refresh the results page
  await page.reload();

  // Verify results page still shows data
  await expect(
    page.getByRole("heading", { name: /Results/i }),
  ).toBeVisible({ timeout: 10_000 });

  // Metric cards should still render
  const metricsAfter = await extractMetricCardValues(page);
  expect(Object.keys(metricsAfter).length).toBeGreaterThan(0);

  // Tabs should still be present
  await results.verifyTabsPresent(["Overview", "Experiments"]);
});
