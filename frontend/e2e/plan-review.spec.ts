/**
 * Plan review HITL tests — approve and revise plans.
 *
 * Requires real backend with GOOGLE_API_KEY.
 */

import { test, expect } from "@playwright/test";
import { DashboardPO, MonitorPO } from "./fixtures/page-objects";

test.skip(!process.env.RUN_LIFECYCLE_TEST, "Set RUN_LIFECYCLE_TEST=1 to run");

test("Approve plan before training begins", async ({ page }) => {
  const dashboard = new DashboardPO(page);
  await dashboard.goto();

  // Submit WITHOUT auto-approve
  await dashboard.objectiveInput.fill(
    "Classify iris species using scikit-learn",
  );
  await dashboard.dataFileInput.fill("iris_data/Iris.csv");
  await dashboard.launchButton.click();

  await expect(page).toHaveURL(/\/monitor\?id=/, { timeout: 10_000 });

  // Wait for plan review panel to appear
  const monitor = new MonitorPO(page);
  await monitor.approvePlan();

  // Training should continue and eventually complete
  await monitor.waitForCompletion(300_000);

  // Should end up on results page
  await expect(page).toHaveURL(/\/results/);
});

test("Request revision then approve", async ({ page }) => {
  const dashboard = new DashboardPO(page);
  await dashboard.goto();

  await dashboard.objectiveInput.fill(
    "Classify iris species with more algorithms",
  );
  await dashboard.dataFileInput.fill("iris_data/Iris.csv");
  await dashboard.launchButton.click();

  await expect(page).toHaveURL(/\/monitor\?id=/, { timeout: 10_000 });

  // Request a revision
  const monitor = new MonitorPO(page);
  await monitor.requestRevision("Try using more ensemble methods like AdaBoost and GradientBoosting");

  // Wait for the revised plan review panel to reappear
  await monitor.approvePlan();

  // Should complete after approval
  await monitor.waitForCompletion(300_000);
  await expect(page).toHaveURL(/\/results/);
});
