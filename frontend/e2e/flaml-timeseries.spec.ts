/**
 * FLAML time series lifecycle: Electric Production dataset end-to-end.
 *
 * Verifies forecast-specific tabs (Forecast, Forecast Errors, Seasonal Profile)
 * plus FLAML-specific tabs (Trial History, Estimators).
 *
 * Requires GOOGLE_API_KEY on the backend and RUN_LIFECYCLE_TEST=1.
 */

import { test, expect } from "@playwright/test";
import { DashboardPO, MonitorPO, ResultsPO, ModelsPO } from "./fixtures/page-objects";
import { getExperiment } from "./fixtures/experiment-api";
import { TIMESERIES_METRICS } from "./fixtures/metric-ranges";
import {
  assertChartInCard,
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

test("FLAML time series: Electric Production end-to-end", async ({ page, request }, testInfo) => {
  const consoleErrors = collectConsoleErrors(page);

  // ── Phase 1: Submit and wait ──────────────────────────────────────────
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

  // ── Phase 2: Metric cards validation ──────────────────────────────────
  const results = new ResultsPO(page);
  const metrics = await extractMetricCardValues(page);

  expect(
    Object.keys(metrics).length,
    "Should have at least one metric card",
  ).toBeGreaterThan(0);

  assertMetricsValid(
    metrics,
    TIMESERIES_METRICS.requiredAny,
    TIMESERIES_METRICS.ranges,
  );

  await screenshotTab(page, testInfo, "overview", "ts-forecast", "flaml");

  // ── Phase 3: Tab presence ─────────────────────────────────────────────
  await results.verifyTabsPresent(["Overview", "Experiments"]);

  // ── Phase 4: Time series-specific chart tabs ──────────────────────────

  // Forecast (ComposedChart in Card)
  if (await results.hasTab("Forecast")) {
    await results.clickTab("Forecast");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await assertChartInCard(page, "Forecast vs Actual");
    // Verify forecast summary card
    await expect(
      page.getByRole("heading", { name: /Forecast Summary/i }).or(
        page.getByText("Total Points"),
      ),
    ).toBeVisible({ timeout: 5_000 });
    await screenshotTab(page, testInfo, "forecast", "ts-forecast", "flaml");
  }

  // Forecast Errors
  if (await results.hasTab("Forecast Errors")) {
    await results.clickTab("Forecast Errors");
    await results.waitForTabContent();
    await waitForChartRender(page);
    // Verify error metric labels
    await expect(
      page.getByText("MAPE").or(page.getByText("RMSE")).or(page.getByText("MAE")),
    ).toBeVisible({ timeout: 5_000 });
    await screenshotTab(page, testInfo, "forecast-errors", "ts-forecast", "flaml");
  }

  // Seasonal Profile
  if (await results.hasTab("Seasonal Profile")) {
    await results.clickTab("Seasonal Profile");
    await results.waitForTabContent();
    await waitForChartRender(page);
    // Verify time series profile card metrics
    await expect(
      page.getByText(/Frequency|Stationarity|Period/i),
    ).toBeVisible({ timeout: 5_000 });
    await screenshotTab(page, testInfo, "seasonal-profile", "ts-forecast", "flaml");
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
    await screenshotTab(page, testInfo, "trial-history", "ts-forecast", "flaml");
  }

  // Estimators
  if (await results.hasTab("Estimators")) {
    await results.clickTab("Estimators");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await assertChartInCard(page, "Estimator Comparison");
    await screenshotTab(page, testInfo, "estimators", "ts-forecast", "flaml");
  }

  // ── Phase 6: Tooltip hover on Forecast ────────────────────────────────
  if (await results.hasTab("Forecast")) {
    await results.clickTab("Forecast");
    await results.waitForTabContent();
    await waitForChartRender(page);
    await hoverChartInCard(page, "Forecast vs Actual");
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
    assertExperimentResult(exp as Record<string, unknown>, "ts_forecast");
  }

  // ── Phase 10: Console error check ─────────────────────────────────────
  expect(
    consoleErrors,
    `Unexpected console errors: ${consoleErrors.join("; ")}`,
  ).toHaveLength(0);
});
