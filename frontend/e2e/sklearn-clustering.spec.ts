/**
 * Sklearn clustering lifecycle: Mall Customers dataset end-to-end.
 *
 * Dashboard -> submit -> Monitor (SSE) -> Results -> verify:
 *   - Metric cards (silhouette score range)
 *   - Clustering-specific chart tabs (Clusters, Elbow, Silhouette, Profiles)
 *   - Tooltip hover interactions
 *   - Visual regression screenshots
 *   - API response structure
 *   - No unexpected console errors
 *
 * Requires GOOGLE_API_KEY on the backend and RUN_LIFECYCLE_TEST=1.
 */

import { test, expect } from "@playwright/test";
import { DashboardPO, MonitorPO, ResultsPO, ModelsPO } from "./fixtures/page-objects";
import { getExperiment } from "./fixtures/experiment-api";
import { CLUSTERING_METRICS } from "./fixtures/metric-ranges";
import {
  assertChartRendered,
  hoverChartElement,
  extractMetricCardValues,
  assertMetricsValid,
  assertExperimentResult,
  screenshotTab,
  waitForChartRender,
  waitForTabContent,
  collectConsoleErrors,
} from "./fixtures/chart-helpers";

test.skip(!process.env.RUN_LIFECYCLE_TEST, "Set RUN_LIFECYCLE_TEST=1 to run");

test("Sklearn clustering: Mall Customers end-to-end", async ({ page, request }, testInfo) => {
  const consoleErrors = collectConsoleErrors(page);

  // ── Phase 1: Submit and wait ──────────────────────────────────────────
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

  // ── Phase 2: Metric cards validation ──────────────────────────────────
  const results = new ResultsPO(page);
  const metrics = await extractMetricCardValues(page);

  expect(
    Object.keys(metrics).length,
    "Should have at least one metric card",
  ).toBeGreaterThan(0);

  assertMetricsValid(
    metrics,
    CLUSTERING_METRICS.requiredAny,
    CLUSTERING_METRICS.ranges,
  );

  await screenshotTab(page, testInfo, "overview", "clustering", "sklearn");

  // ── Phase 3: Tab presence ─────────────────────────────────────────────
  await results.verifyTabsPresent([
    "Overview",
    "Experiments",
    "Plan",
    "Analysis",
    "Summary",
    "Code",
    "Journal",
  ]);

  // ── Phase 4: Clustering-specific chart tabs ───────────────────────────

  // Clusters (ScatterChart via ChartContainer)
  if (await results.hasTab("Clusters")) {
    await results.clickTab("Clusters");
    await results.waitForTabContent();
    await waitForChartRender(page);
    // Verify cluster badges are visible
    await expect(
      page.locator("text=/Cluster \\d+/").first(),
    ).toBeVisible({ timeout: 5_000 });
    await screenshotTab(page, testInfo, "clusters", "clustering", "sklearn");
  }

  // Elbow Curve (LineChart via ChartContainer)
  if (await results.hasTab("Elbow Curve")) {
    await results.clickTab("Elbow Curve");
    await results.waitForTabContent();
    await waitForChartRender(page);
    // Verify "Selected Number of Clusters" or k= badge
    await expect(
      page.getByRole("heading", { name: /Selected Number of Clusters/i }).or(
        page.getByText(/k = \d+/),
      ),
    ).toBeVisible({ timeout: 5_000 });
    await screenshotTab(page, testInfo, "elbow-curve", "clustering", "sklearn");
  }

  // Silhouette (BarChart via ChartContainer)
  if (await results.hasTab("Silhouette")) {
    await results.clickTab("Silhouette");
    await results.waitForTabContent();
    await waitForChartRender(page);
    // Verify silhouette score heading
    await expect(
      page.getByRole("heading", { name: /Silhouette/i }),
    ).toBeVisible({ timeout: 5_000 });
    await screenshotTab(page, testInfo, "silhouette", "clustering", "sklearn");
  }

  // Cluster Profiles (RadarChart via ChartContainer)
  if (await results.hasTab("Cluster Profiles")) {
    await results.clickTab("Cluster Profiles");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await screenshotTab(page, testInfo, "cluster-profiles", "clustering", "sklearn");
  }

  // ── Phase 5: Tooltip hover ────────────────────────────────────────────
  if (await results.hasTab("Clusters")) {
    await results.clickTab("Clusters");
    await results.waitForTabContent();
    await waitForChartRender(page);
    const svg = page.locator('div[role="img"] svg').first();
    const dataEl = svg.locator("circle, path").first();
    if ((await dataEl.count()) > 0) {
      await dataEl.hover({ force: true });
      await page.waitForTimeout(500);
    }
  }

  // ── Phase 6: Click through common tabs ────────────────────────────────
  await results.clickThroughTabs(["Overview", "Plan", "Summary", "Code"]);

  // ── Phase 7: Navigate to Models page ──────────────────────────────────
  const models = new ModelsPO(page);
  await models.goto();

  // ── Phase 8: API response validation ──────────────────────────────────
  const expId = results.getExperimentIdFromUrl() ?? new URL(page.url()).searchParams.get("id");
  if (expId) {
    const exp = await getExperiment(request, expId);
    assertExperimentResult(exp as Record<string, unknown>, "clustering");
  }

  // ── Phase 9: Console error check ──────────────────────────────────────
  expect(
    consoleErrors,
    `Unexpected console errors: ${consoleErrors.join("; ")}`,
  ).toHaveLength(0);
});
