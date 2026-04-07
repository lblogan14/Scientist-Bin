/**
 * Sklearn regression lifecycle: Wine Quality dataset end-to-end.
 */

import { test, expect } from "@playwright/test";
import { DashboardPO, MonitorPO, ResultsPO } from "./fixtures/page-objects";

test.skip(!process.env.RUN_LIFECYCLE_TEST, "Set RUN_LIFECYCLE_TEST=1 to run");

test("Sklearn regression: Wine Quality end-to-end", async ({ page }) => {
  const dashboard = new DashboardPO(page);
  await dashboard.goto();
  await dashboard.fillAndSubmit(
    "Predict wine quality from physicochemical properties",
    "wine_data/WineQT.csv",
    { framework: "sklearn", autoApprove: true },
  );

  await expect(page).toHaveURL(/\/monitor\?id=/, { timeout: 10_000 });

  const monitor = new MonitorPO(page);
  await monitor.waitForCompletion(300_000);

  const results = new ResultsPO(page);
  await results.verifyTabsPresent(["Overview", "Experiments", "Plan", "Summary"]);

  // Regression-specific tabs
  const regressionTabs = ["Predicted vs Actual", "Residuals", "CV Stability", "Features"];
  for (const tab of regressionTabs) {
    if (await results.hasTab(tab)) {
      await results.clickTab(tab);
    }
  }
});
