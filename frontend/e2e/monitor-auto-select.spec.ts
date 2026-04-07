/**
 * Monitor page auto-selection tests.
 *
 * Verifies that navigating to /monitor without a query param
 * auto-selects a running or recent experiment.
 *
 * Requires GOOGLE_API_KEY on the backend and RUN_LIFECYCLE_TEST=1.
 */

import { test, expect } from "@playwright/test";
import { DashboardPO, MonitorPO } from "./fixtures/page-objects";

test.skip(!process.env.RUN_LIFECYCLE_TEST, "Set RUN_LIFECYCLE_TEST=1 to run");

test("Monitor page auto-selects running experiment", async ({ page }) => {
  // Start a training with auto-approve
  const dashboard = new DashboardPO(page);
  await dashboard.goto();
  await dashboard.fillAndSubmit(
    "Classify iris for auto-select e2e test",
    "iris_data/Iris.csv",
    { framework: "sklearn", autoApprove: true },
  );

  await expect(page).toHaveURL(/\/monitor\?id=/, { timeout: 10_000 });

  // Extract the experiment ID from the URL
  const monitorUrl = new URL(page.url());
  const experimentId = monitorUrl.searchParams.get("id");
  expect(experimentId).toBeTruthy();

  // Navigate away, then go to /monitor WITHOUT query params
  await page.goto("/experiments");
  await expect(
    page.getByRole("heading", { name: /Experiments/i }),
  ).toBeVisible();

  await page.goto("/monitor");

  // Monitor should auto-select the running experiment
  // The URL should update to include ?id=
  await expect(page).toHaveURL(/\/monitor\?id=/, { timeout: 15_000 });

  // The objective text should appear somewhere on the page
  await expect(
    page.getByText(/iris/i),
  ).toBeVisible({ timeout: 10_000 });

  // Wait for completion
  const monitor = new MonitorPO(page);
  await monitor.waitForCompletion(300_000);
});
