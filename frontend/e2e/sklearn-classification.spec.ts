/**
 * Sklearn classification lifecycle: Iris dataset end-to-end.
 *
 * Dashboard → submit → Monitor (SSE) → Results → verify classification tabs.
 * Requires GOOGLE_API_KEY on the backend and RUN_LIFECYCLE_TEST=1.
 */

import { test, expect } from "@playwright/test";
import { DashboardPO, MonitorPO, ResultsPO, ModelsPO } from "./fixtures/page-objects";

test.skip(!process.env.RUN_LIFECYCLE_TEST, "Set RUN_LIFECYCLE_TEST=1 to run");

test("Sklearn classification: Iris end-to-end", async ({ page }) => {
  const dashboard = new DashboardPO(page);
  await dashboard.goto();
  await dashboard.fillAndSubmit(
    "Classify iris species using the Iris dataset with scikit-learn",
    "iris_data/Iris.csv",
    { framework: "sklearn", autoApprove: true },
  );

  // Should redirect to monitor page
  await expect(page).toHaveURL(/\/monitor\?id=/, { timeout: 10_000 });

  // Wait for training to complete (redirects to results)
  const monitor = new MonitorPO(page);
  await monitor.waitForCompletion(300_000);

  // Verify classification-specific tabs
  const results = new ResultsPO(page);
  await results.verifyTabsPresent([
    "Overview",
    "Experiments",
    "Plan",
    "Analysis",
    "Summary",
    "Code",
    "Journal",
  ]);

  // Classification-specific tabs (conditional — depend on data availability)
  const classificationTabs = ["Confusion Matrix", "CV Stability", "Features"];
  for (const tab of classificationTabs) {
    if (await results.hasTab(tab)) {
      await results.clickTab(tab);
    }
  }

  // Click through common tabs
  await results.clickThroughTabs(["Overview", "Plan", "Summary", "Code"]);

  // Navigate to Models page
  const models = new ModelsPO(page);
  await models.goto();
});
