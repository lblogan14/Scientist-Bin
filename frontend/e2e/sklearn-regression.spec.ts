/**
 * Sklearn regression lifecycle: Wine Quality dataset end-to-end.
 *
 * Dashboard -> submit -> Monitor (SSE) -> Results -> verify:
 *   - Metric cards (R2, RMSE ranges)
 *   - Regression-specific chart tabs (Predicted vs Actual, Residuals, etc.)
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
import { REGRESSION_METRICS } from "./fixtures/metric-ranges";
import {
  assertChartRendered,
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

test("Sklearn regression: Wine Quality end-to-end", async ({ page, request }, testInfo) => {
  const consoleErrors = collectConsoleErrors(page);

  // ── Phase 1: Submit and wait ──────────────────────────────────────────
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

  // ── Phase 2: Metric cards validation ──────────────────────────────────
  const results = new ResultsPO(page);
  const metrics = await extractMetricCardValues(page);

  expect(
    Object.keys(metrics).length,
    "Should have at least one metric card",
  ).toBeGreaterThan(0);

  assertMetricsValid(
    metrics,
    REGRESSION_METRICS.requiredAny,
    REGRESSION_METRICS.ranges,
  );

  await screenshotTab(page, testInfo, "overview", "regression", "sklearn");

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

  // ── Phase 4: Regression-specific chart tabs ───────────────────────────

  // Predicted vs Actual (ScatterChart via ChartContainer)
  if (await results.hasTab("Predicted vs Actual")) {
    await results.clickTab("Predicted vs Actual");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await assertChartRendered(page, "Actual vs Predicted");
    // Verify R2/RMSE summary cards
    await expect(
      page.getByRole("heading", { name: /R2 Score/i }).or(
        page.getByRole("heading", { name: /RMSE/i }),
      ),
    ).toBeVisible({ timeout: 5_000 });
    await screenshotTab(page, testInfo, "predicted-vs-actual", "regression", "sklearn");
  }

  // Residuals
  if (await results.hasTab("Residuals")) {
    await results.clickTab("Residuals");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await screenshotTab(page, testInfo, "residuals", "regression", "sklearn");
  }

  // Coefficients (conditional — only for linear models)
  if (await results.hasTab("Coefficients")) {
    await results.clickTab("Coefficients");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await screenshotTab(page, testInfo, "coefficients", "regression", "sklearn");
  }

  // Learning Curve (conditional)
  if (await results.hasTab("Learning Curve")) {
    await results.clickTab("Learning Curve");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await screenshotTab(page, testInfo, "learning-curve", "regression", "sklearn");
  }

  // CV Stability (conditional)
  if (await results.hasTab("CV Stability")) {
    await results.clickTab("CV Stability");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await assertChartRendered(page, "CV Fold Distribution");
    await screenshotTab(page, testInfo, "cv-stability", "regression", "sklearn");
  }

  // Features (conditional)
  if (await results.hasTab("Features")) {
    await results.clickTab("Features");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await screenshotTab(page, testInfo, "features", "regression", "sklearn");
  }

  // ── Phase 5: Tooltip hover ────────────────────────────────────────────
  if (await results.hasTab("Predicted vs Actual")) {
    await results.clickTab("Predicted vs Actual");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await hoverChartElement(page, "Actual vs Predicted");
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
    assertExperimentResult(exp as Record<string, unknown>, "regression");
  }

  // ── Phase 9: Console error check ──────────────────────────────────────
  expect(
    consoleErrors,
    `Unexpected console errors: ${consoleErrors.join("; ")}`,
  ).toHaveLength(0);
});
