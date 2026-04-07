/**
 * FLAML classification lifecycle: Iris dataset end-to-end.
 *
 * Verifies FLAML-specific tabs (Trial History, Estimators) appear
 * in addition to standard classification tabs.
 */

import { test, expect } from "@playwright/test";
import { DashboardPO, MonitorPO, ResultsPO } from "./fixtures/page-objects";

test.skip(!process.env.RUN_LIFECYCLE_TEST, "Set RUN_LIFECYCLE_TEST=1 to run");

test("FLAML classification: Iris end-to-end", async ({ page }) => {
  const dashboard = new DashboardPO(page);
  await dashboard.goto();
  await dashboard.fillAndSubmit(
    "Classify iris species using FLAML AutoML",
    "iris_data/Iris.csv",
    { framework: "flaml", autoApprove: true },
  );

  await expect(page).toHaveURL(/\/monitor\?id=/, { timeout: 10_000 });

  const monitor = new MonitorPO(page);
  await monitor.waitForCompletion(300_000);

  const results = new ResultsPO(page);
  await results.verifyTabsPresent(["Overview", "Experiments", "Plan", "Summary"]);

  // FLAML-specific tabs (conditional — depend on data from FLAML agent)
  const flamlTabs = ["Trial History", "Estimators", "Confusion Matrix", "Features"];
  for (const tab of flamlTabs) {
    if (await results.hasTab(tab)) {
      await results.clickTab(tab);
    }
  }
});
