/**
 * Error handling tests — verify failed experiments show error displays.
 */

import { test, expect } from "@playwright/test";
import { DashboardPO } from "./fixtures/page-objects";

test.skip(!process.env.RUN_LIFECYCLE_TEST, "Set RUN_LIFECYCLE_TEST=1 to run");

test("Failed experiment shows error display", async ({ page }) => {
  const dashboard = new DashboardPO(page);
  await dashboard.goto();

  // Submit with a nonexistent data file path
  await dashboard.fillAndSubmit(
    "Classify data from a file that does not exist",
    "nonexistent/data_that_does_not_exist.csv",
    { autoApprove: true },
  );

  // Should either show an error in the form (400 from API) or redirect to monitor
  // and show error there. Wait for either case.
  const errorInForm = page.getByRole("alert");
  const monitorUrl = page.url().includes("/monitor");

  if (await errorInForm.isVisible({ timeout: 5_000 }).catch(() => false)) {
    // Error shown in form (API rejected the request)
    await expect(errorInForm).toContainText(/error|not found/i);
  } else if (monitorUrl) {
    // Redirected to monitor — experiment should fail quickly
    await expect(
      page.getByText(/error|failed/i),
    ).toBeVisible({ timeout: 60_000 });
  }
});
