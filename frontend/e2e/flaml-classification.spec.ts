/**
 * FLAML classification lifecycle: Iris dataset end-to-end.
 *
 * Same classification assertions as sklearn, plus FLAML-specific tabs:
 * Trial History, Estimators.
 *
 * Requires GOOGLE_API_KEY on the backend and RUN_LIFECYCLE_TEST=1.
 */

import { test, expect } from "@playwright/test";
import { DashboardPO, MonitorPO, ResultsPO, ModelsPO } from "./fixtures/page-objects";
import { getExperiment } from "./fixtures/experiment-api";
import { CLASSIFICATION_METRICS } from "./fixtures/metric-ranges";
import {
  assertChartRendered,
  assertChartInCard,
  assertHeatmapRendered,
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

test("FLAML classification: Iris end-to-end", async ({ page, request }, testInfo) => {
  const consoleErrors = collectConsoleErrors(page);

  // ── Phase 1: Submit and wait ──────────────────────────────────────────
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

  await screenshotTab(page, testInfo, "overview", "classification", "flaml");

  // ── Phase 3: Tab presence ─────────────────────────────────────────────
  await results.verifyTabsPresent(["Overview", "Experiments"]);

  // ── Phase 4: Classification-specific chart tabs ───────────────────────

  // Confusion Matrix (CSS grid heatmap)
  if (await results.hasTab("Confusion Matrix")) {
    await results.clickTab("Confusion Matrix");
    await results.waitForTabContent();
    await assertHeatmapRendered(page, 9);
    await screenshotTab(page, testInfo, "confusion-matrix", "classification", "flaml");
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
    await screenshotTab(page, testInfo, "features", "classification", "flaml");
  }

  // ── Phase 5: FLAML-specific tabs ──────────────────────────────────────

  // Trial History (Card-based, not ChartContainer)
  if (await results.hasTab("Trial History")) {
    await results.clickTab("Trial History");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await assertChartInCard(page, "Trial Convergence");
    // Verify summary metrics
    await expect(page.getByText("Total Trials")).toBeVisible({ timeout: 5_000 });
    await expect(page.getByText("Best Loss")).toBeVisible({ timeout: 5_000 });
    await expect(page.getByText("Best Estimator")).toBeVisible({ timeout: 5_000 });
    await screenshotTab(page, testInfo, "trial-history", "classification", "flaml");
  }

  // Estimators (Card-based)
  if (await results.hasTab("Estimators")) {
    await results.clickTab("Estimators");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await assertChartInCard(page, "Estimator Comparison");
    await screenshotTab(page, testInfo, "estimators", "classification", "flaml");
  }

  // ── Phase 6: Tooltip hover on Trial History ───────────────────────────
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
    assertExperimentResult(exp as Record<string, unknown>, "classification");
  }

  // ── Phase 10: Console error check ─────────────────────────────────────
  expect(
    consoleErrors,
    `Unexpected console errors: ${consoleErrors.join("; ")}`,
  ).toHaveLength(0);
});
