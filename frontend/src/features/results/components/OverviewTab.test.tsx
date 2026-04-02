import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { OverviewTab } from "./OverviewTab";
import type { ExperimentResult } from "@/types/api";

function makeResult(overrides: Partial<ExperimentResult> = {}): ExperimentResult {
  return {
    framework: "sklearn",
    plan: null,
    plan_markdown: null,
    generated_code: null,
    evaluation_results: null,
    experiment_history: [],
    data_profile: null,
    problem_type: "classification",
    iterations: 3,
    analysis_report: null,
    summary_report: null,
    best_model: null,
    best_hyperparameters: null,
    test_metrics: null,
    test_diagnostics: null,
    selection_reasoning: null,
    report_sections: null,
    status: "completed",
    ...overrides,
  };
}

describe("OverviewTab", () => {
  it("renders executive summary when present", () => {
    const result = makeResult({
      report_sections: {
        title: "Report",
        executive_summary: "This experiment achieved strong results.",
        dataset_overview: "",
        methodology: "",
        model_comparison_table: "",
        cv_stability_analysis: "",
        best_model_analysis: "",
        feature_importance_analysis: "",
        hyperparameter_analysis: "",
        error_analysis: "",
        conclusions: "",
        recommendations: [],
        reproducibility_notes: "",
      },
    });
    render(<OverviewTab result={result} />);
    expect(screen.getByText("Executive Summary")).toBeInTheDocument();
    expect(
      screen.getByText("This experiment achieved strong results."),
    ).toBeInTheDocument();
  });

  it("renders best model name when present", () => {
    const result = makeResult({
      best_model: "RandomForestClassifier",
      problem_type: "classification",
    });
    render(<OverviewTab result={result} />);
    expect(screen.getByText("Best Model")).toBeInTheDocument();
    expect(screen.getByText("RandomForestClassifier")).toBeInTheDocument();
    expect(screen.getByText("classification")).toBeInTheDocument();
  });

  it("renders selection reasoning when present", () => {
    const result = makeResult({
      selection_reasoning: "RF was selected for highest F1 score.",
    });
    render(<OverviewTab result={result} />);
    expect(screen.getByText("Why This Model?")).toBeInTheDocument();
    expect(
      screen.getByText("RF was selected for highest F1 score."),
    ).toBeInTheDocument();
  });

  it("handles minimal result without crashing", () => {
    const result = makeResult();
    const { container } = render(<OverviewTab result={result} />);
    // Should render without errors, just an empty div
    expect(container.firstChild).toBeInTheDocument();
  });
});
