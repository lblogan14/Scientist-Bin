/**
 * Reusable Page Object Models for Playwright E2E tests.
 *
 * Centralizes selectors so lifecycle tests stay DRY and resilient
 * to minor UI changes.
 */

import type { Page, Locator } from "@playwright/test";
import { expect } from "@playwright/test";

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

export class DashboardPO {
  readonly page: Page;
  readonly objectiveInput: Locator;
  readonly dataFileInput: Locator;
  readonly frameworkTrigger: Locator;
  readonly autoApproveSwitch: Locator;
  readonly deepResearchSwitch: Locator;
  readonly launchButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.objectiveInput = page.getByRole("textbox", { name: "Objective" });
    this.dataFileInput = page.getByRole("textbox", {
      name: /dataset file path/i,
    });
    this.frameworkTrigger = page.locator(
      '[id="radix-"] >> text=Auto-detect',
    ).or(page.getByRole("combobox").first());
    this.autoApproveSwitch = page.getByRole("switch", {
      name: /auto-approve/i,
    });
    this.deepResearchSwitch = page.getByRole("switch", {
      name: /deep research/i,
    });
    this.launchButton = page.getByRole("button", {
      name: /launch training/i,
    });
  }

  async goto() {
    await this.page.goto("/");
    await expect(
      this.page.getByRole("heading", { name: "Dashboard" }),
    ).toBeVisible();
  }

  /** Check if the ActiveExperimentBanner is visible on the dashboard. */
  async isActiveBannerVisible(): Promise<boolean> {
    return this.page
      .getByText("Plan Review Needed")
      .isVisible({ timeout: 5_000 })
      .catch(() => false);
  }

  /** Click the "Review Plan" link in the active experiment banner. */
  async clickActiveBannerReviewLink() {
    await this.page.getByRole("link", { name: /Review Plan/i }).click();
  }

  async selectFramework(name: "sklearn" | "flaml" | "auto") {
    // Open the Select dropdown
    const trigger = this.page
      .locator("button")
      .filter({ has: this.page.locator('[role="combobox"]') })
      .or(this.page.getByRole("combobox").first());
    await trigger.click();

    const labels: Record<string, string> = {
      sklearn: "Scikit-learn",
      flaml: "FLAML (AutoML)",
      auto: "Auto-detect",
    };
    await this.page.getByRole("option", { name: labels[name] }).click();
  }

  async fillAndSubmit(
    objective: string,
    dataFile: string,
    opts: {
      framework?: "sklearn" | "flaml" | "auto";
      autoApprove?: boolean;
    } = {},
  ) {
    await this.objectiveInput.fill(objective);
    await this.dataFileInput.fill(dataFile);

    if (opts.framework && opts.framework !== "auto") {
      await this.selectFramework(opts.framework);
    }

    if (opts.autoApprove) {
      const checked = await this.autoApproveSwitch.isChecked();
      if (!checked) await this.autoApproveSwitch.click();
    }

    await this.launchButton.click();
  }
}

// ---------------------------------------------------------------------------
// Training Monitor
// ---------------------------------------------------------------------------

export class MonitorPO {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async isLive(): Promise<boolean> {
    return this.page.getByText(/^Live$/).isVisible({ timeout: 5_000 });
  }

  async waitForCompletion(timeoutMs = 300_000) {
    // Wait for redirect to /results (triggered by experiment_done SSE event)
    await this.page.waitForURL(/\/results/, { timeout: timeoutMs });
  }

  async approvePlan() {
    const approveBtn = this.page.getByRole("button", {
      name: /approve plan/i,
    });
    await expect(approveBtn).toBeVisible({ timeout: 120_000 });
    await approveBtn.click();
  }

  async requestRevision(feedback: string) {
    const reviseBtn = this.page.getByRole("button", {
      name: /request revision/i,
    });
    await expect(reviseBtn).toBeVisible({ timeout: 120_000 });
    await reviseBtn.click();

    const textarea = this.page.getByRole("textbox", {
      name: /feedback|revision/i,
    });
    await textarea.fill(feedback);

    await this.page
      .getByRole("button", { name: /submit feedback/i })
      .click();
  }
}

// ---------------------------------------------------------------------------
// Results
// ---------------------------------------------------------------------------

export class ResultsPO {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async clickTab(name: string) {
    const tab = this.page.getByRole("tab", { name });
    if (await tab.isVisible()) {
      await tab.click();
      // Wait for content to load (lazy tabs)
      await this.page.waitForTimeout(500);
    }
  }

  async getVisibleTabs(): Promise<string[]> {
    const tabs = this.page.getByRole("tab");
    const count = await tabs.count();
    const names: string[] = [];
    for (let i = 0; i < count; i++) {
      const text = await tabs.nth(i).textContent();
      if (text) names.push(text.trim());
    }
    return names;
  }

  async hasTab(name: string): Promise<boolean> {
    return this.page.getByRole("tab", { name }).isVisible();
  }

  async verifyTabsPresent(expectedTabs: string[]) {
    for (const tab of expectedTabs) {
      await expect(
        this.page.getByRole("tab", { name: tab }),
      ).toBeVisible();
    }
  }

  async clickThroughTabs(tabNames: string[]) {
    for (const name of tabNames) {
      const tab = this.page.getByRole("tab", { name });
      if (await tab.isVisible()) {
        await tab.click();
        await this.page.waitForTimeout(500);
      }
    }
  }

  /**
   * After clicking a tab, wait for the active TabsContent to have
   * visible content (Suspense resolved, spinner gone).
   */
  async waitForTabContent(timeout = 10_000) {
    const activePanel = this.page.locator(
      'div[role="tabpanel"][data-state="active"]',
    );
    await expect(activePanel).toBeVisible({ timeout });
    // Wait for Loading spinner to disappear
    await expect(async () => {
      const loading = await activePanel
        .locator("text=Loading...")
        .isVisible()
        .catch(() => false);
      expect(loading).toBe(false);
    }).toPass({ timeout });
  }

  /** Extract the experiment ID from the current URL query params. */
  getExperimentIdFromUrl(): string | null {
    const url = new URL(this.page.url());
    return url.searchParams.get("id");
  }
}

// ---------------------------------------------------------------------------
// Models
// ---------------------------------------------------------------------------

export class ModelsPO {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto() {
    await this.page.goto("/models");
    await expect(
      this.page.getByRole("heading", { name: "Models", exact: true }),
    ).toBeVisible();
  }

  async hasModelCards(): Promise<boolean> {
    // ModelRankingCard renders cards with algorithm names
    const cards = this.page.locator('[class*="card"]');
    return (await cards.count()) > 0;
  }
}

// ---------------------------------------------------------------------------
// Experiments List
// ---------------------------------------------------------------------------

export class ExperimentsPO {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto() {
    await this.page.goto("/experiments");
    await expect(
      this.page.getByRole("heading", { name: /Experiments/i }),
    ).toBeVisible();
  }

  async filterByStatus(status: string) {
    // Status dropdown shows "All statuses" by default
    await this.page.getByText("All statuses").click();
    await this.page.getByRole("option", { name: new RegExp(status, "i") }).click();
  }

  async filterByFramework(framework: string) {
    await this.page.getByText("All frameworks").click();
    await this.page.getByRole("option", { name: new RegExp(framework, "i") }).click();
  }

  async filterByProblemType(problemType: string) {
    await this.page.getByText("All types").click();
    await this.page.getByRole("option", { name: new RegExp(problemType, "i") }).click();
  }

  async searchExperiments(query: string) {
    await this.page.getByPlaceholder(/Search experiments/).fill(query);
  }

  async clearSearch() {
    await this.page.getByPlaceholder(/Search experiments/).clear();
  }

  /** Count visible experiment rows (excludes "no experiments" placeholder). */
  async getVisibleRowCount(): Promise<number> {
    const rows = this.page.locator("tbody tr").filter({
      hasNot: this.page.locator("text=No experiments"),
    });
    return rows.count();
  }

  /** Parse the "Showing X of Y experiments" text. */
  async getShowingCount(): Promise<{ showing: number; total: number }> {
    const text = await this.page
      .locator("text=/Showing \\d+ of \\d+/")
      .textContent()
      .catch(() => null);
    const match = text?.match(/Showing (\d+) of (\d+)/);
    return {
      showing: match ? parseInt(match[1]) : 0,
      total: match ? parseInt(match[2]) : 0,
    };
  }

  /** Click on an experiment row by its ID. */
  async clickExperimentRow(experimentId: string) {
    await this.page
      .locator("tr")
      .filter({ hasText: experimentId.slice(0, 12) })
      .first()
      .click();
  }

  /** Click on an experiment row by objective text. */
  async clickExperimentByObjective(objective: string) {
    await this.page
      .locator("tr")
      .filter({ hasText: objective })
      .first()
      .click();
  }
}
