import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { DashboardStats } from "./DashboardStats";
import type { Experiment, ExperimentResult } from "@/types/api";

// Mock the useExperiments hook
const mockUseExperiments = vi.fn();
vi.mock("../hooks/use-experiments", () => ({
  useExperiments: () => mockUseExperiments(),
}));

function makeExperiment(
  overrides: Partial<Experiment> = {},
): Experiment {
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
    created_at: "2026-04-01T00:00:00Z",
    updated_at: "2026-04-01T00:00:00Z",
    ...overrides,
  };
}

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

describe("DashboardStats", () => {
  it("renders skeleton cards when loading", () => {
    mockUseExperiments.mockReturnValue({ data: undefined, isLoading: true });
    const { container } = render(<DashboardStats />);
    // 5 skeleton cards, Card uses data-slot="card"
    const cards = container.querySelectorAll('[data-slot="card"]');
    expect(cards.length).toBe(5);
  });

  it("returns null when experiments is empty", () => {
    mockUseExperiments.mockReturnValue({ data: [], isLoading: false });
    const { container } = render(<DashboardStats />);
    expect(container.firstChild).toBeNull();
  });

  it("returns null when experiments is undefined (after load)", () => {
    mockUseExperiments.mockReturnValue({ data: undefined, isLoading: false });
    const { container } = render(<DashboardStats />);
    expect(container.firstChild).toBeNull();
  });

  it("renders all 5 stat cards with experiment data", () => {
    const experiments = [
      makeExperiment({ id: "1", status: "completed" }),
      makeExperiment({ id: "2", status: "running" }),
      makeExperiment({ id: "3", status: "completed" }),
    ];
    mockUseExperiments.mockReturnValue({ data: experiments, isLoading: false });

    render(<DashboardStats />);

    expect(screen.getByText("Total Experiments")).toBeInTheDocument();
    expect(screen.getByText("Running")).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText("Avg Best Accuracy")).toBeInTheDocument();
    expect(screen.getByText("Avg Training Time")).toBeInTheDocument();
  });

  it("displays correct counts", () => {
    const experiments = [
      makeExperiment({ id: "1", status: "completed" }),
      makeExperiment({ id: "2", status: "running" }),
      makeExperiment({ id: "3", status: "completed" }),
      makeExperiment({ id: "4", status: "pending" }),
    ];
    mockUseExperiments.mockReturnValue({ data: experiments, isLoading: false });

    render(<DashboardStats />);

    // Total: 4, Running: 1, Completed: 2
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("computes and displays average accuracy from experiment history", () => {
    const result1 = makeResult({
      experiment_history: [
        {
          iteration: 1,
          algorithm: "RF",
          hyperparameters: {},
          metrics: { accuracy: 0.9 },
          training_time_seconds: 5,
          timestamp: "2026-04-01T00:00:00Z",
        },
      ],
    });
    const result2 = makeResult({
      experiment_history: [
        {
          iteration: 1,
          algorithm: "SVC",
          hyperparameters: {},
          metrics: { accuracy: 0.8 },
          training_time_seconds: 3,
          timestamp: "2026-04-01T00:00:00Z",
        },
      ],
    });

    const experiments = [
      makeExperiment({ id: "1", status: "completed", result: result1 }),
      makeExperiment({ id: "2", status: "completed", result: result2 }),
    ];
    mockUseExperiments.mockReturnValue({ data: experiments, isLoading: false });

    render(<DashboardStats />);

    // Avg accuracy: (0.9 + 0.8) / 2 = 0.85 -> "0.8500"
    expect(screen.getByText("0.8500")).toBeInTheDocument();
  });

  it("shows dash for accuracy when no metrics available", () => {
    const result = makeResult({ experiment_history: [] });
    const experiments = [
      makeExperiment({ id: "1", status: "completed", result: result }),
    ];
    mockUseExperiments.mockReturnValue({ data: experiments, isLoading: false });

    render(<DashboardStats />);

    // Average accuracy should show "-" when no accuracy data
    const dashes = screen.getAllByText("-");
    expect(dashes.length).toBeGreaterThanOrEqual(1);
  });
});
