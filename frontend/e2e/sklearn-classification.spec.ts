/**
 * Sklearn classification lifecycle: Iris dataset end-to-end.
 *
 * Dashboard -> submit -> Monitor (SSE) -> Results -> verify:
 *   - Metric cards (values, ranges)
 *   - Classification-specific chart tabs (SVG rendering, data presence)
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
import { CLASSIFICATION_METRICS } from "./fixtures/metric-ranges";
import {
  assertChartRendered,
  assertHeatmapRendered,
  assertChartInCard,
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

test("Sklearn classification: Iris end-to-end", async ({ page, request }, testInfo) => {
  const consoleErrors = collectConsoleErrors(page);

  // ── Phase 1: Submit and wait ──────────────────────────────────────────
  const dashboard = new DashboardPO(page);
  await dashboard.goto();
  await dashboard.fillAndSubmit(
    "Classify iris species using the Iris dataset with scikit-learn",
    "iris_data/Iris.csv",
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
    CLASSIFICATION_METRICS.requiredAny,
    CLASSIFICATION_METRICS.ranges,
  );

  // Screenshot: overview with metric cards
  await screenshotTab(page, testInfo, "overview", "classification", "sklearn");

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

  // ── Phase 4: Classification-specific chart tabs ───────────────────────

  // Confusion Matrix (CSS grid heatmap, NOT SVG)
  if (await results.hasTab("Confusion Matrix")) {
    await results.clickTab("Confusion Matrix");
    await results.waitForTabContent();
    await assertHeatmapRendered(page, 9); // 3x3 grid = 9 cells for Iris
    await screenshotTab(page, testInfo, "confusion-matrix", "classification", "sklearn");
  }

  // CV Stability (BoxPlotChart via ChartContainer)
  if (await results.hasTab("CV Stability")) {
    await results.clickTab("CV Stability");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await assertChartRendered(page, "CV Fold Distribution");
    // Verify table has algorithm rows with numeric mean/std
    await expect(page.getByRole("columnheader", { name: /Mean/i })).toBeVisible();
    await screenshotTab(page, testInfo, "cv-stability", "classification", "sklearn");
  }

  // Overfitting tab
  if (await results.hasTab("Overfitting")) {
    await results.clickTab("Overfitting");
    await results.waitForTabContent();
    await waitForChartRender(page);
    // Overfitting tab has a risk table with badges
    await expect(page.getByRole("columnheader", { name: /Risk/i }).or(
      page.getByText(/Overfit|Risk/i),
    )).toBeVisible({ timeout: 5_000 });
    await screenshotTab(page, testInfo, "overfitting", "classification", "sklearn");
  }

  // Features (FeatureImportanceChart via ChartContainer)
  if (await results.hasTab("Features")) {
    await results.clickTab("Features");
    await results.waitForTabContent();
    await waitForChartRender(page);
    // Feature table should have at least 4 rows (Iris has 4 features)
    const featureRows = page.getByRole("row").filter({
      has: page.locator("td"),
    });
    await expect(async () => {
      expect(await featureRows.count()).toBeGreaterThanOrEqual(4);
    }).toPass({ timeout: 5_000 });
    await screenshotTab(page, testInfo, "features", "classification", "sklearn");
  }

  // Hyperparams (if available)
  if (await results.hasTab("Hyperparams")) {
    await results.clickTab("Hyperparams");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await screenshotTab(page, testInfo, "hyperparams", "classification", "sklearn");
  }

  // ── Phase 5: Tooltip hover on a chart ─────────────────────────────────
  if (await results.hasTab("CV Stability")) {
    await results.clickTab("CV Stability");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await hoverChartElement(page, "CV Fold Distribution");
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
    assertExperimentResult(exp as Record<string, unknown>, "classification");
  }

  // ── Phase 9: Console error check ──────────────────────────────────────
  expect(
    consoleErrors,
    `Unexpected console errors: ${consoleErrors.join("; ")}`,
  ).toHaveLength(0);
});
