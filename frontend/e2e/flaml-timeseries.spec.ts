/**
 * FLAML time series lifecycle: Electric Production dataset end-to-end.
 *
 * Verifies forecast-specific tabs (Forecast, Forecast Errors, Seasonal Profile).
 */

import { test, expect } from "@playwright/test";
import { DashboardPO, MonitorPO, ResultsPO } from "./fixtures/page-objects";

test.skip(!process.env.RUN_LIFECYCLE_TEST, "Set RUN_LIFECYCLE_TEST=1 to run");

test("FLAML time series: Electric Production end-to-end", async ({ page }) => {
  const dashboard = new DashboardPO(page);
  await dashboard.goto();
  await dashboard.fillAndSubmit(
    "Forecast monthly electric production from historical data",
    "electric_data/Electric_Production.csv",
    { framework: "flaml", autoApprove: true },
  );

  await expect(page).toHaveURL(/\/monitor\?id=/, { timeout: 10_000 });

  const monitor = new MonitorPO(page);
  await monitor.waitForCompletion(300_000);

  const results = new ResultsPO(page);
  await results.verifyTabsPresent(["Overview", "Experiments"]);

  // Time series + FLAML-specific tabs
  const tsTabs = ["Forecast", "Forecast Errors", "Seasonal Profile", "Trial History", "Estimators"];
  for (const tab of tsTabs) {
    if (await results.hasTab(tab)) {
      await results.clickTab(tab);
    }
  }
});
