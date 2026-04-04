import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MemoryRouter } from "react-router";
import { ModelComparisonTable } from "./ModelComparisonTable";
import type { Experiment, ExperimentResult } from "@/types/api";

function makeResult(
  overrides: Partial<ExperimentResult> = {},
): ExperimentResult {
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

function makeExperiment(overrides: Partial<Experiment> = {}): Experiment {
  return {
    id: "exp-1",
    objective: "Classify iris",
    data_description: "",
    data_file_path: null,
    framework: "sklearn",
    status: "completed",
    phase: "done",
    runs: [],
    best_run_id: null,
    iteration_count: 3,
    progress_events: [],
    result: null,
    execution_plan: null,
    analysis_report: null,
    summary_report: null,
    split_data_paths: null,
    problem_type: null,
    created_at: "2026-04-01T00:00:00Z",
    updated_at: "2026-04-01T00:00:00Z",
    ...overrides,
  };
}

function renderWithRouter(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe("ModelComparisonTable", () => {
  it("renders table headers", () => {
    renderWithRouter(<ModelComparisonTable models={[]} />);

    expect(screen.getByText("Objective")).toBeInTheDocument();
    expect(screen.getByText("Algorithm")).toBeInTheDocument();
    expect(screen.getByText("Iter")).toBeInTheDocument();
    expect(screen.getByText("Time (s)")).toBeInTheDocument();
  });

  it("renders experiment rows from history", () => {
    const result = makeResult({
      experiment_history: [
        {
          iteration: 1,
          algorithm: "RandomForest",
          hyperparameters: {},
          metrics: { accuracy: 0.95 },
          training_time_seconds: 2.5,
          timestamp: "2026-04-01T00:00:00Z",
        },
        {
          iteration: 2,
          algorithm: "GradientBoosting",
          hyperparameters: {},
          metrics: { accuracy: 0.93 },
          training_time_seconds: 5.1,
          timestamp: "2026-04-01T00:00:00Z",
        },
      ],
    });
    const model = makeExperiment({
      id: "exp-1",
      objective: "Classify iris",
      result: result,
    });

    renderWithRouter(<ModelComparisonTable models={[model]} />);

    expect(screen.getByText("RandomForest")).toBeInTheDocument();
    expect(screen.getByText("GradientBoosting")).toBeInTheDocument();
    expect(screen.getByText("0.9500")).toBeInTheDocument();
    expect(screen.getByText("0.9300")).toBeInTheDocument();
  });

  it("handles empty models array", () => {
    renderWithRouter(<ModelComparisonTable models={[]} />);

    // Table headers should still be present
    expect(screen.getByText("Objective")).toBeInTheDocument();
    // No rows in the body
    const tbody = document.querySelector("tbody");
    expect(tbody).toBeInTheDocument();
    expect(tbody!.children.length).toBe(0);
  });

  it("creates fallback rows for experiments without history", () => {
    const model = makeExperiment({
      id: "exp-1",
      objective: "Predict prices",
      framework: "sklearn",
      result: makeResult({ experiment_history: [] }),
    });

    renderWithRouter(<ModelComparisonTable models={[model]} />);

    expect(screen.getByText("Predict prices")).toBeInTheDocument();
    expect(screen.getByText("sklearn")).toBeInTheDocument();
  });

  it("shows metric columns from experiment data", () => {
    const result = makeResult({
      experiment_history: [
        {
          iteration: 1,
          algorithm: "RF",
          hyperparameters: {},
          metrics: { accuracy: 0.95, f1: 0.93 },
          training_time_seconds: 1.0,
          timestamp: "2026-04-01T00:00:00Z",
        },
      ],
    });
    const model = makeExperiment({ result });

    renderWithRouter(<ModelComparisonTable models={[model]} />);

    expect(screen.getByText("accuracy")).toBeInTheDocument();
    expect(screen.getByText("f1")).toBeInTheDocument();
  });

  it("renders Results links pointing to correct experiment", () => {
    const result = makeResult({
      experiment_history: [
        {
          iteration: 1,
          algorithm: "RF",
          hyperparameters: {},
          metrics: { accuracy: 0.95 },
          training_time_seconds: 1.0,
          timestamp: "2026-04-01T00:00:00Z",
        },
      ],
    });
    const model = makeExperiment({ id: "exp-abc", result });

    renderWithRouter(<ModelComparisonTable models={[model]} />);

    const link = screen.getByText("Results");
    expect(link.closest("a")).toHaveAttribute("href", "/results?id=exp-abc");
  });

  it("limits metric columns to 4", () => {
    const result = makeResult({
      experiment_history: [
        {
          iteration: 1,
          algorithm: "RF",
          hyperparameters: {},
          metrics: {
            accuracy: 0.95,
            f1: 0.93,
            precision: 0.94,
            recall: 0.92,
            roc_auc: 0.97,
            log_loss: 0.1,
          },
          training_time_seconds: 1.0,
          timestamp: "2026-04-01T00:00:00Z",
        },
      ],
    });
    const model = makeExperiment({ result });

    renderWithRouter(<ModelComparisonTable models={[model]} />);

    // Should show at most 4 metric columns in the header
    const headerCells = document.querySelectorAll("thead th");
    // Objective + Algorithm + Iter + (up to 4 metrics) + Time (s) + empty = max 9
    // With 4 metric columns: 3 fixed + 4 metrics + 1 time + 1 empty = 9
    expect(headerCells.length).toBeLessThanOrEqual(9);
  });
});
