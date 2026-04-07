/**
 * Chart validation helpers for Playwright E2E tests.
 *
 * Provides utilities for asserting Recharts SVG rendering,
 * extracting metric card values, hovering for tooltips,
 * and taking standardised screenshots.
 */

import type { Page, TestInfo } from "@playwright/test";
import { expect } from "@playwright/test";
import type { MetricRange } from "./metric-ranges";

// ---------------------------------------------------------------------------
// Recharts animation wait
// ---------------------------------------------------------------------------

/** Wait for Recharts SVG animations to settle. */
export async function waitForChartRender(page: Page, ms = 1500) {
  await page.waitForTimeout(ms);
}

// ---------------------------------------------------------------------------
// Chart presence assertions
// ---------------------------------------------------------------------------

/**
 * Assert that a chart wrapped in ChartContainer renders SVG content.
 *
 * ChartContainer renders: <div role="img" aria-label="{title}"> <svg>…</svg> </div>
 */
export async function assertChartRendered(page: Page, ariaLabel: string) {
  const container = page.locator(
    `div[role="img"][aria-label="${ariaLabel}"]`,
  );

  // Wait for the container + SVG to appear
  await expect(container).toBeVisible({ timeout: 10_000 });
  const svg = container.locator("svg").first();
  await expect(svg).toBeVisible({ timeout: 5_000 });

  // Verify SVG has meaningful child elements (not just an empty svg tag)
  await expect(async () => {
    const childCount = await svg
      .locator("g, rect, path, circle, line, text")
      .count();
    expect(childCount).toBeGreaterThan(0);
  }).toPass({ timeout: 5_000 });
}

/**
 * Assert that a chart inside a Card (without ChartContainer wrapper) renders SVG.
 *
 * Locates the Card by its heading text, then finds the SVG within.
 * Used for ForecastPlotTab, TrialHistoryTab, EstimatorComparisonTab, etc.
 */
export async function assertChartInCard(page: Page, cardHeading: string) {
  const heading = page.getByRole("heading", {
    name: new RegExp(cardHeading, "i"),
  });
  await expect(heading).toBeVisible({ timeout: 10_000 });

  // Walk up to the Card element, then find svg inside
  // Card structure: <Card><CardHeader><CardTitle>heading</></><CardContent>...<svg>...</></Card>
  const card = heading.locator("xpath=ancestor::div[contains(@class,'card')]");
  const svg = card.locator("svg").first();

  await expect(svg).toBeVisible({ timeout: 5_000 });

  await expect(async () => {
    const childCount = await svg
      .locator("g, rect, path, circle, line, text")
      .count();
    expect(childCount).toBeGreaterThan(0);
  }).toPass({ timeout: 5_000 });
}

/**
 * Assert that the ConfusionMatrix heatmap (CSS grid, NOT SVG) renders.
 *
 * Heatmap cells have title attributes: "True: X, Predicted: Y, Count: Z"
 */
export async function assertHeatmapRendered(
  page: Page,
  minCells = 4,
) {
  const cells = page.locator('div[title^="True:"]');

  await expect(async () => {
    const count = await cells.count();
    expect(count).toBeGreaterThanOrEqual(minCells);
  }).toPass({ timeout: 10_000 });
}

// ---------------------------------------------------------------------------
// Tooltip / hover interactions
// ---------------------------------------------------------------------------

/**
 * Hover over the first data element in a ChartContainer-wrapped chart
 * and verify a tooltip-like element appears.
 */
export async function hoverChartElement(page: Page, ariaLabel: string) {
  const container = page.locator(
    `div[role="img"][aria-label="${ariaLabel}"]`,
  );
  const svg = container.locator("svg").first();

  // Find the first interactive data element
  const dataElement = svg
    .locator("rect, circle, path.recharts-scatter-symbol")
    .first();

  if ((await dataElement.count()) > 0) {
    await dataElement.hover({ force: true });
    // Give tooltip time to appear
    await page.waitForTimeout(500);
  }
}

/**
 * Hover over the first data element in a Card-based chart.
 */
export async function hoverChartInCard(page: Page, cardHeading: string) {
  const heading = page.getByRole("heading", {
    name: new RegExp(cardHeading, "i"),
  });
  const card = heading.locator("xpath=ancestor::div[contains(@class,'card')]");
  const svg = card.locator("svg").first();

  const dataElement = svg.locator("rect, circle, path").first();
  if ((await dataElement.count()) > 0) {
    await dataElement.hover({ force: true });
    await page.waitForTimeout(500);
  }
}

// ---------------------------------------------------------------------------
// Metric card extraction
// ---------------------------------------------------------------------------

/**
 * Extract metric name→value pairs from the MetricCards component.
 *
 * MetricCards renders:
 *   <Card><CardHeader><CardTitle class="text-xs">KEY</></><CardContent><p class="text-2xl font-bold">VALUE</p></></Card>
 */
export async function extractMetricCardValues(
  page: Page,
): Promise<Record<string, number>> {
  const result: Record<string, number> = {};

  // Wait for metric cards grid to be visible
  const grid = page.locator("div.grid").filter({
    has: page.locator("p.text-2xl.font-bold"),
  });

  if ((await grid.count()) === 0) return result;

  // Each Card has a CardTitle (metric name) and a <p> (metric value)
  const cards = grid.first().locator(":scope > div");
  const count = await cards.count();

  for (let i = 0; i < count; i++) {
    const card = cards.nth(i);
    const keyEl = card.locator(".text-xs.font-medium.uppercase").first();
    const valEl = card.locator("p.text-2xl.font-bold").first();

    if (
      (await keyEl.count()) > 0 &&
      (await valEl.count()) > 0
    ) {
      const key = (await keyEl.textContent())?.trim().toLowerCase() ?? "";
      const valText = (await valEl.textContent())?.trim() ?? "";
      const num = parseFloat(valText);
      if (key && !isNaN(num)) {
        result[key] = num;
      }
    }
  }

  return result;
}

// ---------------------------------------------------------------------------
// Metric validation
// ---------------------------------------------------------------------------

/**
 * Assert that metrics contain at least one required key and all values
 * fall within the specified ranges.
 */
export function assertMetricsValid(
  metrics: Record<string, number>,
  requiredAny: string[],
  ranges: Record<string, MetricRange>,
) {
  // At least one required metric must be present
  const metricKeys = Object.keys(metrics);
  const hasRequired = requiredAny.some((k) =>
    metricKeys.some((mk) => mk.includes(k)),
  );
  expect(
    hasRequired,
    `Expected at least one of [${requiredAny.join(", ")}] in metrics: [${metricKeys.join(", ")}]`,
  ).toBe(true);

  // All present metrics must not be NaN and must be in range (if range defined)
  for (const [key, value] of Object.entries(metrics)) {
    expect(value, `Metric "${key}" should not be NaN`).not.toBeNaN();

    // Check range if defined (case-insensitive key match)
    const rangeKey = Object.keys(ranges).find((rk) =>
      key.toLowerCase().includes(rk.toLowerCase()),
    );
    if (rangeKey) {
      const { min, max } = ranges[rangeKey];
      expect(
        value,
        `Metric "${key}" = ${value} should be >= ${min}`,
      ).toBeGreaterThanOrEqual(min);
      if (max !== Infinity) {
        expect(
          value,
          `Metric "${key}" = ${value} should be <= ${max}`,
        ).toBeLessThanOrEqual(max);
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Screenshots
// ---------------------------------------------------------------------------

/**
 * Take a standardised screenshot of the current tab view.
 *
 * Naming: {framework}-{problemType}-{tabName}.png
 */
export async function screenshotTab(
  page: Page,
  testInfo: TestInfo,
  tabName: string,
  problemType: string,
  framework: string,
) {
  const name = `${framework}-${problemType}-${tabName}.png`;
  await page.screenshot({
    path: testInfo.outputPath(name),
    fullPage: false,
  });
  // Attach to the test report
  await testInfo.attach(name, {
    path: testInfo.outputPath(name),
    contentType: "image/png",
  });
}

// ---------------------------------------------------------------------------
// Tab content wait
// ---------------------------------------------------------------------------

/**
 * Wait for the active tab content to finish loading (Suspense resolved).
 *
 * After clicking a tab, the content is lazy-loaded. This waits for the
 * active TabsContent to have visible content that isn't just a spinner.
 */
export async function waitForTabContent(page: Page, timeout = 10_000) {
  const activeContent = page.locator(
    'div[role="tabpanel"][data-state="active"]',
  );
  await expect(activeContent).toBeVisible({ timeout });

  // Wait until the spinner/loading state is gone
  await expect(async () => {
    const hasSpinner = await activeContent
      .locator("text=Loading...")
      .isVisible()
      .catch(() => false);
    expect(hasSpinner).toBe(false);
  }).toPass({ timeout });
}

// ---------------------------------------------------------------------------
// Console error collection
// ---------------------------------------------------------------------------

/**
 * Collect console errors during test execution.
 * Call at test start, then check errors at the end.
 */
export function collectConsoleErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      const text = msg.text();
      // Filter out known benign errors
      if (
        !text.includes("net::ERR") &&
        !text.includes("Failed to fetch") &&
        !text.includes("404") &&
        !text.includes("ERR_CONNECTION_REFUSED") &&
        !text.includes("Unauthorized")
      ) {
        errors.push(text);
      }
    }
  });
  return errors;
}

// ---------------------------------------------------------------------------
// API result validation
// ---------------------------------------------------------------------------

/**
 * Validate experiment result structure from the API.
 */
export function assertExperimentResult(
  experiment: Record<string, unknown>,
  expectedProblemType: string,
) {
  expect(experiment.status).toBe("completed");

  const result = experiment.result as Record<string, unknown> | null;
  expect(result).not.toBeNull();

  // Problem type
  expect(result!.problem_type).toBe(expectedProblemType);

  // Generated code must exist
  expect(result!.generated_code).toBeTruthy();

  // Experiment history must have at least one entry
  const history = result!.experiment_history as unknown[];
  expect(history?.length).toBeGreaterThanOrEqual(1);

  // Evaluation results with metrics
  const evalResults = result!.evaluation_results as Record<
    string,
    unknown
  > | null;
  expect(evalResults).not.toBeNull();
  expect(evalResults!.metrics).toBeTruthy();
}
