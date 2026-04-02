import { test, expect } from "@playwright/test";

test.describe("Full lifecycle: Dashboard -> Monitor -> Results -> Models", () => {
  test("Dashboard page loads and shows form", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: "Dashboard" }),
    ).toBeVisible();
    // Objective form should be present
    await expect(page.getByText("New Training Experiment")).toBeVisible();
    await expect(page.getByRole("textbox", { name: "Objective" })).toBeVisible();
  });

  test("Dashboard form validation works", async ({ page }) => {
    await page.goto("/");
    // Fill short objective
    await page.getByRole("textbox", { name: "Objective" }).fill("short");
    await page.getByRole("button", { name: /launch training/i }).click();
    // Should show validation error
    await expect(page.getByText(/at least 10 characters/i)).toBeVisible();
  });

  test("Experiments page loads", async ({ page }) => {
    await page.goto("/experiments");
    await expect(
      page.getByRole("heading", { name: /experiments/i }),
    ).toBeVisible();
  });

  test("Training Monitor page loads", async ({ page }) => {
    await page.goto("/monitor");
    // Should show either a running experiment or empty state
    await expect(
      page
        .getByRole("heading", { name: /training/i })
        .or(page.getByText(/no.*experiment/i)),
    ).toBeVisible();
  });

  test("Results page loads", async ({ page }) => {
    await page.goto("/results");
    // Should show results or empty state
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

  test("Navigation via sidebar works", async ({ page }) => {
    await page.goto("/");

    // Navigate to Experiments
    await page.getByRole("link", { name: "Experiments" }).click();
    await expect(page).toHaveURL(/\/experiments/);

    // Navigate to Training
    await page.getByRole("link", { name: "Training" }).click();
    await expect(page).toHaveURL(/\/monitor/);

    // Navigate to Results
    await page.getByRole("link", { name: "Results" }).click();
    await expect(page).toHaveURL(/\/results/);

    // Navigate to Models
    await page.getByRole("link", { name: "Models" }).click();
    await expect(page).toHaveURL(/\/models/);

    // Navigate back to Dashboard
    await page.getByRole("link", { name: "Dashboard" }).click();
    await expect(page).toHaveURL("/");
  });

  test("Health indicator shows backend status", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Backend healthy")).toBeVisible();
  });

  test("Unknown route redirects to dashboard", async ({ page }) => {
    await page.goto("/nonexistent-page");
    await expect(page).toHaveURL("/");
  });

  test("No console errors on page load", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        errors.push(msg.text());
      }
    });

    // Visit each page
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

    // Filter out expected errors (like 404 for missing experiments, network errors)
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
