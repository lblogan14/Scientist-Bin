/**
 * FLAML regression lifecycle: Wine Quality dataset end-to-end.
 */

import { test, expect } from "@playwright/test";
import { DashboardPO, MonitorPO, ResultsPO } from "./fixtures/page-objects";

test.skip(!process.env.RUN_LIFECYCLE_TEST, "Set RUN_LIFECYCLE_TEST=1 to run");

test("FLAML regression: Wine Quality end-to-end", async ({ page }) => {
  const dashboard = new DashboardPO(page);
  await dashboard.goto();
  await dashboard.fillAndSubmit(
    "Predict wine quality using FLAML AutoML",
    "wine_data/WineQT.csv",
    { framework: "flaml", autoApprove: true },
  );

  await expect(page).toHaveURL(/\/monitor\?id=/, { timeout: 10_000 });

  const monitor = new MonitorPO(page);
  await monitor.waitForCompletion(300_000);

  const results = new ResultsPO(page);
  await results.verifyTabsPresent(["Overview", "Experiments"]);

  const tabs = ["Predicted vs Actual", "Trial History", "Estimators", "Features"];
  for (const tab of tabs) {
    if (await results.hasTab(tab)) {
      await results.clickTab(tab);
    }
  }
});
