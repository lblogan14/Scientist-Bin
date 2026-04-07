/**
 * Theme switching smoke tests.
 *
 * Verifies Light / Dark / Science theme toggling, CSS class application,
 * localStorage persistence, and cross-navigation consistency.
 * No backend required.
 */

import { test, expect } from "@playwright/test";

test.describe("Theme switching", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: "Dashboard" }),
    ).toBeVisible();
  });

  async function openThemeMenu(page: import("@playwright/test").Page) {
    // Theme dropdown is in the header — the last icon button
    const themeBtn = page.locator("header button").last();
    await themeBtn.click();
  }

  test("Switch to Dark theme", async ({ page }) => {
    await openThemeMenu(page);
    await page.getByRole("menuitem", { name: /Dark/i }).click();

    const htmlClass = await page.locator("html").getAttribute("class");
    expect(htmlClass).toContain("dark");
  });

  test("Switch to Science theme", async ({ page }) => {
    await openThemeMenu(page);
    await page.getByRole("menuitem", { name: /Science/i }).click();

    const htmlClass = await page.locator("html").getAttribute("class");
    expect(htmlClass).toContain("science");
    expect(htmlClass).not.toContain("dark");
  });

  test("Switch back to Light theme", async ({ page }) => {
    // First switch to dark
    await openThemeMenu(page);
    await page.getByRole("menuitem", { name: /Dark/i }).click();
    expect(await page.locator("html").getAttribute("class")).toContain("dark");

    // Then switch back to light
    await openThemeMenu(page);
    await page.getByRole("menuitem", { name: /Light/i }).click();

    const htmlClass = await page.locator("html").getAttribute("class") ?? "";
    expect(htmlClass).not.toContain("dark");
    expect(htmlClass).not.toContain("science");
  });

  test("Theme persists after page refresh", async ({ page }) => {
    await openThemeMenu(page);
    await page.getByRole("menuitem", { name: /Dark/i }).click();
    expect(await page.locator("html").getAttribute("class")).toContain("dark");

    // Verify localStorage
    const stored = await page.evaluate(() =>
      localStorage.getItem("scientist-bin-theme"),
    );
    expect(stored).toBe("dark");

    // Refresh and verify
    await page.reload();
    await expect(
      page.getByRole("heading", { name: "Dashboard" }),
    ).toBeVisible();
    expect(await page.locator("html").getAttribute("class")).toContain("dark");
  });

  test("Theme persists across navigation", async ({ page }) => {
    await openThemeMenu(page);
    await page.getByRole("menuitem", { name: /Science/i }).click();
    expect(await page.locator("html").getAttribute("class")).toContain(
      "science",
    );

    // Navigate to Experiments via sidebar
    await page.getByRole("link", { name: /Experiments/i }).click();
    await expect(
      page.getByRole("heading", { name: /Experiments/i }),
    ).toBeVisible();

    // Theme should still be applied
    expect(await page.locator("html").getAttribute("class")).toContain(
      "science",
    );
  });
});
