/**
 * Navigation smoke tests.
 *
 * Verifies browser back/forward navigation and direct URL access
 * for all application routes. No backend required.
 */

import { test, expect } from "@playwright/test";

test.describe("Navigation", () => {
  test("Back/forward browser navigation", async ({ page }) => {
    // Visit each page in sequence
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();

    await page.getByRole("link", { name: /Experiments/i }).click();
    await expect(page.getByRole("heading", { name: /Experiments/i })).toBeVisible();

    await page.getByRole("link", { name: /Training/i }).click();
    await expect(page.getByRole("heading", { name: /Training/i })).toBeVisible();

    await page.getByRole("link", { name: /Results/i }).click();
    // Results may show "No experiments yet" or "Results" heading
    await expect(
      page.getByRole("heading", { name: /Results/i }).or(
        page.getByText(/No experiments yet/i),
      ),
    ).toBeVisible();

    await page.getByRole("link", { name: /Models/i }).click();
    await expect(page.getByRole("heading", { name: /Models/i })).toBeVisible();

    // Go back through the history
    await page.goBack(); // → Results
    await expect(page).toHaveURL(/\/results/);

    await page.goBack(); // → Monitor
    await expect(page).toHaveURL(/\/monitor/);

    await page.goBack(); // → Experiments
    await expect(page).toHaveURL(/\/experiments/);

    await page.goBack(); // → Dashboard
    await expect(page).toHaveURL(/\/$/);

    // Go forward
    await page.goForward(); // → Experiments
    await expect(page).toHaveURL(/\/experiments/);

    await page.goForward(); // → Monitor
    await expect(page).toHaveURL(/\/monitor/);
  });

  test("Direct URL navigation for all routes", async ({ page }) => {
    const routes = [
      { path: "/", heading: "Dashboard" },
      { path: "/experiments", heading: "Experiments" },
      { path: "/monitor", heading: "Training" },
      { path: "/models", heading: "Models" },
    ];

    for (const route of routes) {
      await page.goto(route.path);
      await expect(
        page.getByRole("heading", { name: new RegExp(route.heading, "i") }),
      ).toBeVisible({ timeout: 5_000 });
    }

    // Results page may show empty state
    await page.goto("/results");
    await expect(
      page.getByRole("heading", { name: /Results/i }).or(
        page.getByText(/No experiments yet/i),
      ),
    ).toBeVisible({ timeout: 5_000 });
  });

  test("No blank states during rapid navigation", async ({ page }) => {
    await page.goto("/");

    // Rapidly navigate between pages
    const links = ["Experiments", "Training", "Results", "Models", "Dashboard"];
    for (const linkName of links) {
      await page.getByRole("link", { name: new RegExp(linkName, "i") }).click();
      // Verify the page has some content (not a white screen)
      const bodyText = await page.locator("body").textContent();
      expect(bodyText?.length).toBeGreaterThan(0);
    }
  });
});
