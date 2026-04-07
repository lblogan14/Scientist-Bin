/**
 * Sidebar notification dot tests.
 *
 * Verifies the amber pulsing dot on the Training sidebar item when
 * an experiment is waiting for plan review.
 *
 * Requires GOOGLE_API_KEY on the backend and RUN_LIFECYCLE_TEST=1.
 */

import { test, expect } from "@playwright/test";
import { MonitorPO } from "./fixtures/page-objects";
import { seedPlanReviewExperiment } from "./fixtures/experiment-seed";

test.skip(!process.env.RUN_LIFECYCLE_TEST, "Set RUN_LIFECYCLE_TEST=1 to run");

let experimentId: string;
let cleanup: () => Promise<void>;

test.beforeAll(async ({ request }) => {
  const seeded = await seedPlanReviewExperiment(request, {
    objective: "Classify iris for sidebar notification e2e test",
    dataFile: "iris_data/Iris.csv",
  });
  experimentId = seeded.id;
  cleanup = seeded.cleanup;
});

test.afterAll(async () => {
  await cleanup();
});

test("Sidebar shows amber dot when plan review pending", async ({ page }) => {
  // Navigate to experiments page (not monitor) so sidebar is visible
  await page.goto("/experiments");
  await expect(
    page.getByRole("heading", { name: /Experiments/i }),
  ).toBeVisible();

  // Wait for sidebar poll to detect plan_review (polls every 10s)
  // The amber dot: <span class="size-2 shrink-0 animate-pulse rounded-full bg-amber-500" />
  const trainingLink = page.getByRole("link", { name: /Training/i });
  const amberDot = trainingLink.locator("span.animate-pulse");

  await expect(amberDot).toBeVisible({ timeout: 20_000 });

  // Click Training → navigate to monitor
  await trainingLink.click();
  await expect(page).toHaveURL(/\/monitor/, { timeout: 5_000 });

  // Plan review panel should be visible
  const approveBtn = page.getByRole("button", { name: /approve plan/i });
  await expect(approveBtn).toBeVisible({ timeout: 30_000 });

  // Approve the plan
  const monitor = new MonitorPO(page);
  await monitor.approvePlan();

  // Wait for completion
  await monitor.waitForCompletion(300_000);

  // Navigate away and check that dot is gone
  await page.goto("/experiments");
  await expect(
    page.getByRole("heading", { name: /Experiments/i }),
  ).toBeVisible();

  // Dot should no longer be visible (poll will update)
  await expect(amberDot).not.toBeVisible({ timeout: 20_000 });
});
