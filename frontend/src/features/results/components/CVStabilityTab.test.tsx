import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { CVStabilityTab } from "./CVStabilityTab";
import type { ChartData, ExperimentRecord } from "@/types/api";

describe("CVStabilityTab", () => {
  it("shows no-data message when no CV data is available", () => {
    render(<CVStabilityTab />);
    expect(
      screen.getByText("No cross-validation fold data available for this experiment."),
    ).toBeInTheDocument();
  });

  it("renders table with algorithm stats from chartData", () => {
    const chartData: ChartData = {
      cv_fold_scores: {
        RandomForest: {
          accuracy: { scores: [0.92, 0.94, 0.91, 0.93, 0.95], mean: 0.93 },
        },
      },
    };
    render(<CVStabilityTab chartData={chartData} />);
    // Algorithm name may appear in both chart stats and table
    expect(screen.getAllByText("RandomForest").length).toBeGreaterThanOrEqual(1);
    // Table headers (may appear multiple times due to chart stats table)
    expect(screen.getAllByText("Algorithm").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Mean").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Stability")).toBeInTheDocument();
  });

  it("renders from experiment history fallback", () => {
    const history: ExperimentRecord[] = [
      {
        iteration: 1,
        algorithm: "SVM",
        hyperparameters: {},
        metrics: { accuracy: 0.88 },
        training_time_seconds: 5,
        timestamp: "2026-04-01T10:00:00Z",
        cv_fold_scores: { accuracy: [0.85, 0.88, 0.9, 0.87, 0.89] },
      },
    ];
    render(<CVStabilityTab history={history} />);
    // Algorithm name appears in both chart and table
    expect(screen.getAllByText("SVM").length).toBeGreaterThanOrEqual(1);
  });
});
