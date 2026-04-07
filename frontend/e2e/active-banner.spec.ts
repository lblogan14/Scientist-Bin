/**
 * Active experiment banner tests.
 *
 * Submits an experiment without auto-approve, waits for plan_review phase,
 * then verifies the ActiveExperimentBanner on the dashboard.
 *
 * Requires GOOGLE_API_KEY on the backend and RUN_LIFECYCLE_TEST=1.
 */

import { test, expect } from "@playwright/test";
import { DashboardPO, MonitorPO } from "./fixtures/page-objects";
import { seedPlanReviewExperiment } from "./fixtures/experiment-seed";
import { deleteExperiment } from "./fixtures/experiment-api";

test.skip(!process.env.RUN_LIFECYCLE_TEST, "Set RUN_LIFECYCLE_TEST=1 to run");

let experimentId: string;
let cleanup: () => Promise<void>;

test.beforeAll(async ({ request }) => {
  const seeded = await seedPlanReviewExperiment(request, {
    objective: "Classify iris for banner e2e test",
    dataFile: "iris_data/Iris.csv",
  });
  experimentId = seeded.id;
  cleanup = seeded.cleanup;
});

test.afterAll(async () => {
  await cleanup();
});

test("Active experiment banner shows for plan_review", async ({ page }) => {
  const dashboard = new DashboardPO(page);
  await dashboard.goto();

  // Banner should show "Plan Review Needed"
  const bannerVisible = await dashboard.isActiveBannerVisible();
  expect(bannerVisible, "ActiveExperimentBanner should be visible").toBe(true);

  // Click "Review Plan" link
  await dashboard.clickActiveBannerReviewLink();

  // Should navigate to monitor page
  await expect(page).toHaveURL(/\/monitor/, { timeout: 10_000 });

  // Plan review panel should be visible
  const monitor = new MonitorPO(page);
  const approveBtn = page.getByRole("button", { name: /approve plan/i });
  await expect(approveBtn).toBeVisible({ timeout: 30_000 });

  // Approve the plan so it doesn't hang
  await monitor.approvePlan();
  await monitor.waitForCompletion(300_000);
});
