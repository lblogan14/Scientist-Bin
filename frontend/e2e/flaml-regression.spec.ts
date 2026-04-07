/**
 * FLAML regression lifecycle: Wine Quality dataset end-to-end.
 *
 * Same regression assertions as sklearn, plus FLAML-specific tabs:
 * Trial History, Estimators.
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
  hoverChartInCard,
  extractMetricCardValues,
  assertMetricsValid,
  assertExperimentResult,
  screenshotTab,
  waitForChartRender,
  waitForTabContent,
  collectConsoleErrors,
} from "./fixtures/chart-helpers";

test.skip(!process.env.RUN_LIFECYCLE_TEST, "Set RUN_LIFECYCLE_TEST=1 to run");

test("FLAML regression: Wine Quality end-to-end", async ({ page, request }, testInfo) => {
  const consoleErrors = collectConsoleErrors(page);

  // ── Phase 1: Submit and wait ──────────────────────────────────────────
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

  await screenshotTab(page, testInfo, "overview", "regression", "flaml");

  // ── Phase 3: Tab presence ─────────────────────────────────────────────
  await results.verifyTabsPresent(["Overview", "Experiments"]);

  // ── Phase 4: Regression-specific chart tabs ───────────────────────────

  // Predicted vs Actual
  if (await results.hasTab("Predicted vs Actual")) {
    await results.clickTab("Predicted vs Actual");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await assertChartRendered(page, "Actual vs Predicted");
    await screenshotTab(page, testInfo, "predicted-vs-actual", "regression", "flaml");
  }

  // Residuals
  if (await results.hasTab("Residuals")) {
    await results.clickTab("Residuals");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await screenshotTab(page, testInfo, "residuals", "regression", "flaml");
  }

  // CV Stability
  if (await results.hasTab("CV Stability")) {
    await results.clickTab("CV Stability");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await assertChartRendered(page, "CV Fold Distribution");
  }

  // Features
  if (await results.hasTab("Features")) {
    await results.clickTab("Features");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await screenshotTab(page, testInfo, "features", "regression", "flaml");
  }

  // ── Phase 5: FLAML-specific tabs ──────────────────────────────────────

  // Trial History
  if (await results.hasTab("Trial History")) {
    await results.clickTab("Trial History");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await assertChartInCard(page, "Trial Convergence");
    await expect(page.getByText("Total Trials")).toBeVisible({ timeout: 5_000 });
    await expect(page.getByText("Best Estimator")).toBeVisible({ timeout: 5_000 });
    await screenshotTab(page, testInfo, "trial-history", "regression", "flaml");
  }

  // Estimators
  if (await results.hasTab("Estimators")) {
    await results.clickTab("Estimators");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await assertChartInCard(page, "Estimator Comparison");
    await screenshotTab(page, testInfo, "estimators", "regression", "flaml");
  }

  // ── Phase 6: Tooltip hover ────────────────────────────────────────────
  if (await results.hasTab("Trial History")) {
    await results.clickTab("Trial History");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await hoverChartInCard(page, "Trial Convergence");
  }

  // ── Phase 7: Click through common tabs ────────────────────────────────
  await results.clickThroughTabs(["Overview", "Plan", "Summary", "Code"]);

  // ── Phase 8: Navigate to Models page ──────────────────────────────────
  const models = new ModelsPO(page);
  await models.goto();

  // ── Phase 9: API response validation ──────────────────────────────────
  const expId = results.getExperimentIdFromUrl() ?? new URL(page.url()).searchParams.get("id");
  if (expId) {
    const exp = await getExperiment(request, expId);
    assertExperimentResult(exp as Record<string, unknown>, "regression");
  }

  // ── Phase 10: Console error check ─────────────────────────────────────
  expect(
    consoleErrors,
    `Unexpected console errors: ${consoleErrors.join("; ")}`,
  ).toHaveLength(0);
});
