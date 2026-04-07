import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [["html", { open: "never" }], ["list"]],
  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "smoke",
      testMatch: [
        "smoke.spec.ts",
        "framework-selection.spec.ts",
        "theme-switching.spec.ts",
        "navigation.spec.ts",
      ],
      timeout: 60_000,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "lifecycle",
      testMatch: [
        "sklearn-*.spec.ts",
        "flaml-*.spec.ts",
        "plan-review.spec.ts",
        "error-handling.spec.ts",
        "artifacts.spec.ts",
        "model-selection.spec.ts",
        "experiment-filtering.spec.ts",
        "experiment-detail.spec.ts",
        "active-banner.spec.ts",
        "sidebar-notification.spec.ts",
        "page-refresh.spec.ts",
        "download-buttons.spec.ts",
        "monitor-auto-select.spec.ts",
        "deep-link-results.spec.ts",
      ],
      timeout: 600_000,
      use: {
        ...devices["Desktop Chrome"],
      },
      expect: {
        toHaveScreenshot: {
          maxDiffPixelRatio: 0.02,
          threshold: 0.3,
          animations: "disabled",
        },
      },
    },
  ],
  webServer: [
    {
      command:
        "cd ../backend && uv run uvicorn scientist_bin_backend.main:app --port 8000",
      port: 8000,
      timeout: 30_000,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: "pnpm dev",
      port: 5173,
      timeout: 15_000,
      reuseExistingServer: !process.env.CI,
    },
  ],
});
