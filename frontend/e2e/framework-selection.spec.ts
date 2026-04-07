/**
 * Framework selection dropdown tests.
 *
 * Verifies the framework dropdown on the Dashboard form shows the correct
 * options, including disabled future frameworks.
 */

import { test, expect } from "@playwright/test";

test.describe("Framework selection dropdown", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("New Training Experiment")).toBeVisible();
  });

  test("Shows all framework options", async ({ page }) => {
    // The framework Select renders as a combobox button
    const trigger = page.getByRole("combobox").first();
    await trigger.click();

    // Verify all options
    await expect(
      page.getByRole("option", { name: "Auto-detect" }),
    ).toBeVisible();
    await expect(
      page.getByRole("option", { name: "Scikit-learn" }),
    ).toBeVisible();
    await expect(
      page.getByRole("option", { name: /FLAML/i }),
    ).toBeVisible();
    await expect(
      page.getByRole("option", { name: /PyTorch/i }),
    ).toBeVisible();
    await expect(
      page.getByRole("option", { name: /TensorFlow/i }),
    ).toBeVisible();
  });

  test("Can select FLAML framework", async ({ page }) => {
    const trigger = page.getByRole("combobox").first();
    await trigger.click();
    await page.getByRole("option", { name: /FLAML/i }).click();

    // Verify the combobox trigger now shows the selection
    await expect(trigger).toHaveText(/FLAML/i);
  });

  test("Can select Scikit-learn framework", async ({ page }) => {
    const trigger = page.getByRole("combobox").first();
    await trigger.click();
    await page.getByRole("option", { name: "Scikit-learn" }).click();

    await expect(trigger).toHaveText(/Scikit-learn/);
  });
});
