/**
 * Sklearn clustering lifecycle: Mall Customers dataset end-to-end.
 */

import { test, expect } from "@playwright/test";
import { DashboardPO, MonitorPO, ResultsPO } from "./fixtures/page-objects";

test.skip(!process.env.RUN_LIFECYCLE_TEST, "Set RUN_LIFECYCLE_TEST=1 to run");

test("Sklearn clustering: Mall Customers end-to-end", async ({ page }) => {
  const dashboard = new DashboardPO(page);
  await dashboard.goto();
  await dashboard.fillAndSubmit(
    "Segment mall customers into groups based on spending and income",
    "mall_data/Mall_Customers.csv",
    { framework: "sklearn", autoApprove: true },
  );

  await expect(page).toHaveURL(/\/monitor\?id=/, { timeout: 10_000 });

  const monitor = new MonitorPO(page);
  await monitor.waitForCompletion(300_000);

  const results = new ResultsPO(page);
  await results.verifyTabsPresent(["Overview", "Experiments", "Plan", "Summary"]);

  // Clustering-specific tabs
  const clusteringTabs = ["Clusters", "Elbow Curve", "Silhouette", "Cluster Profiles"];
  for (const tab of clusteringTabs) {
    if (await results.hasTab(tab)) {
      await results.clickTab(tab);
    }
  }
});
