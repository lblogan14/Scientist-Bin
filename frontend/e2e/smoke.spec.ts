/**
 * Smoke tests — fast checks that run on every PR.
 *
 * Verifies page loads, navigation, form validation, and basic UI elements.
 * Does NOT require GOOGLE_API_KEY or real training.
 */

import { test, expect } from "@playwright/test";

test.describe("Page loads", () => {
  test("Dashboard loads and shows form", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: "Dashboard" }),
    ).toBeVisible();
    await expect(page.getByText("New Training Experiment")).toBeVisible();
    await expect(
      page.getByRole("textbox", { name: "Objective" }),
    ).toBeVisible();
  });

  test("Experiments page loads", async ({ page }) => {
    await page.goto("/experiments");
    await expect(
      page.getByRole("heading", { name: /experiments/i }),
    ).toBeVisible();
  });

  test("Training Monitor page loads", async ({ page }) => {
    await page.goto("/monitor");
    await expect(
      page
        .getByRole("heading", { name: /training/i })
        .or(page.getByText(/no.*experiment/i)),
    ).toBeVisible();
  });

  test("Results page loads", async ({ page }) => {
    await page.goto("/results");
    await expect(
      page
        .getByRole("heading", { name: /results/i })
        .or(page.getByText(/no experiments yet/i)),
    ).toBeVisible();
  });

  test("Models page loads", async ({ page }) => {
    await page.goto("/models");
    await expect(
      page.getByRole("heading", { name: "Models", exact: true }),
    ).toBeVisible();
  });
});

test.describe("Navigation", () => {
  test("Sidebar navigation works", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("link", { name: "Experiments" }).click();
    await expect(page).toHaveURL(/\/experiments/);

    await page.getByRole("link", { name: "Training" }).click();
    await expect(page).toHaveURL(/\/monitor/);

    await page.getByRole("link", { name: "Results" }).click();
    await expect(page).toHaveURL(/\/results/);

    await page.getByRole("link", { name: "Models" }).click();
    await expect(page).toHaveURL(/\/models/);

    await page.getByRole("link", { name: "Dashboard" }).click();
    await expect(page).toHaveURL("/");
  });

  test("Unknown route redirects to dashboard", async ({ page }) => {
    await page.goto("/nonexistent-page");
    await expect(page).toHaveURL("/");
  });
});

test.describe("Health & stability", () => {
  test("Health indicator shows backend status", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Backend healthy")).toBeVisible();
  });

  test("No console errors on page load", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        errors.push(msg.text());
      }
    });

    for (const path of [
      "/",
      "/experiments",
      "/monitor",
      "/results",
      "/models",
    ]) {
      await page.goto(path);
      await page.waitForLoadState("networkidle");
    }

    const unexpectedErrors = errors.filter(
      (e) =>
        !e.includes("404") &&
        !e.includes("Failed to fetch") &&
        !e.includes("net::ERR") &&
        !e.includes("HTTPError"),
    );
    expect(unexpectedErrors).toHaveLength(0);
  });
});

test.describe("Form interactions", () => {
  test("Dashboard form validation works", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("textbox", { name: "Objective" }).fill("short");
    await page.getByRole("button", { name: /launch training/i }).click();
    await expect(page.getByText(/at least 10 characters/i)).toBeVisible();
  });

  test("Auto-approve switch toggles correctly", async ({ page }) => {
    await page.goto("/");
    const toggle = page.getByRole("switch", { name: /auto-approve/i });
    await expect(toggle).toBeVisible();

    // Default off
    await expect(toggle).not.toBeChecked();
    await toggle.click();
    await expect(toggle).toBeChecked();
    await toggle.click();
    await expect(toggle).not.toBeChecked();
  });

  test("Deep Research toggle enables budget fields", async ({ page }) => {
    await page.goto("/");
    const toggle = page.getByRole("switch", { name: /deep research/i });
    await toggle.click();

    // Budget fields should appear
    await expect(page.getByText("Advanced Campaign Settings")).toBeVisible();
    await expect(page.getByLabel("Max iterations")).toBeVisible();
    await expect(page.getByLabel("Time limit (hours)")).toBeVisible();
  });
});
