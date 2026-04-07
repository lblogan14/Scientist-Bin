/**
 * Legacy full training lifecycle test with Iris dataset.
 *
 * This test is superseded by the per-framework lifecycle specs
 * (sklearn-classification.spec.ts, flaml-classification.spec.ts, etc.)
 * and the smoke tests in smoke.spec.ts. Kept for backward compatibility
 * with existing CI references.
 */

import { test, expect } from "@playwright/test";

test.describe("Full training lifecycle with Iris dataset", () => {
  test.skip(
    !process.env.RUN_LIFECYCLE_TEST,
    "Set RUN_LIFECYCLE_TEST=1 to run full lifecycle",
  );

  test("Submit, monitor, and view results", async ({ page }) => {
    // 1. Submit training from Dashboard
    await page.goto("/");
    await page.getByRole("textbox", { name: "Objective" }).fill(
      "Classify iris species using the Iris dataset with scikit-learn",
    );
    await page
      .getByRole("textbox", { name: /dataset file path/i })
      .fill("iris_data/Iris.csv");

    // Enable auto-approve
    const autoApproveToggle = page.getByRole("switch", {
      name: /auto-approve/i,
    });
    if (await autoApproveToggle.isVisible()) {
      await autoApproveToggle.click();
    }

    await page.getByRole("button", { name: /launch training/i }).click();

    // 2. Should redirect to monitor page
    await expect(page).toHaveURL(/\/monitor\?id=/, { timeout: 10_000 });

    // 3. Wait for training to complete (up to 5 minutes)
    await expect(page.getByText(/done/i)).toBeVisible({ timeout: 300_000 });

    // 4. Should eventually redirect to results
    await page.waitForURL(/\/results/, { timeout: 30_000 });

    // 5. Click through result tabs
    const tabs = [
      "Overview",
      "Experiments",
      "Plan",
      "Analysis",
      "Summary",
      "Code",
      "Journal",
    ];
    for (const tabName of tabs) {
      const tab = page.getByRole("tab", { name: tabName });
      if (await tab.isVisible()) {
        await tab.click();
        await page.waitForTimeout(500);
      }
    }

    // 6. Navigate to Models page
    await page.goto("/models");
    await expect(page.getByText(/iris/i)).toBeVisible({ timeout: 5_000 });
  });
});
