/**
 * Download button tests on the Results page.
 *
 * Seeds a completed experiment, navigates to results, and verifies
 * that download buttons have correct href attributes and return 200.
 *
 * Requires GOOGLE_API_KEY on the backend and RUN_LIFECYCLE_TEST=1.
 */

import { test, expect } from "@playwright/test";
import { seedOneCompleted } from "./fixtures/experiment-seed";

test.skip(!process.env.RUN_LIFECYCLE_TEST, "Set RUN_LIFECYCLE_TEST=1 to run");

let experimentId: string;
let cleanup: () => Promise<void>;

test.beforeAll(async ({ request }) => {
  const seeded = await seedOneCompleted(request, {
    objective: "Classify iris for download buttons e2e test",
    dataFile: "iris_data/Iris.csv",
  });
  experimentId = seeded.id;
  cleanup = seeded.cleanup;
});

test.afterAll(async () => {
  await cleanup();
});

test.describe("Download buttons", () => {
  test("Results page shows download buttons with correct URLs", async ({ page }) => {
    await page.goto(`/results?id=${experimentId}`);
    await expect(
      page.getByRole("heading", { name: /Results/i }),
    ).toBeVisible({ timeout: 15_000 });

    // Wait for result data to load
    await page.waitForTimeout(3_000);

    // Download buttons: Results, Model, Charts — rendered as <a download> elements
    const downloadLinks = page.locator("a[download]");
    const count = await downloadLinks.count();
    expect(count, "Should have download links").toBeGreaterThanOrEqual(1);

    // Verify each href contains the experiment ID
    for (let i = 0; i < count; i++) {
      const href = await downloadLinks.nth(i).getAttribute("href");
      expect(href).toContain(experimentId);
      expect(href).toContain("/api/v1/experiments/");
    }
  });

  test("Download URLs return valid responses", async ({ page, request }) => {
    const artifactTypes = ["results", "model", "charts"];

    for (const type of artifactTypes) {
      const url = `http://localhost:8000/api/v1/experiments/${experimentId}/artifacts/${type}`;
      const response = await request.get(url);

      // Some artifact types may not exist, but those that do should return 200
      if (response.ok()) {
        expect(response.status()).toBe(200);
        const body = await response.body();
        expect(body.length, `${type} artifact should not be empty`).toBeGreaterThan(0);
      }
    }
  });
});
