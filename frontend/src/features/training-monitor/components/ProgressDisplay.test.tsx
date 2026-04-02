import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ProgressDisplay } from "./ProgressDisplay";
import type { Experiment } from "@/types/api";

function makeExperiment(
  overrides: Partial<Experiment> = {},
): Experiment {
  return {
    id: "test-exp-1",
    objective: "Classify iris species",
    data_description: "",
    data_file_path: null,
    framework: "sklearn",
    status: "running",
    phase: "execution",
    runs: [],
    best_run_id: null,
    iteration_count: 3,
    progress_events: [],
    result: null,
    execution_plan: null,
    analysis_report: null,
    summary_report: null,
    split_data_paths: null,
    created_at: "2026-04-01T10:00:00Z",
    updated_at: "2026-04-01T10:30:00Z",
    ...overrides,
  };
}

describe("ProgressDisplay", () => {
  it("renders experiment objective", () => {
    render(<ProgressDisplay experiment={makeExperiment()} />);
    expect(screen.getByText("Classify iris species")).toBeInTheDocument();
  });

  it("shows running status badge", () => {
    render(<ProgressDisplay experiment={makeExperiment({ status: "running" })} />);
    expect(screen.getByText("running")).toBeInTheDocument();
  });

  it("shows current phase badge", () => {
    render(<ProgressDisplay experiment={makeExperiment({ phase: "planning" })} />);
    expect(screen.getByText("planning")).toBeInTheDocument();
  });

  it("renders all 8 pipeline phase labels", () => {
    render(<ProgressDisplay experiment={makeExperiment()} />);
    const phases = ["Classify", "EDA", "Plan", "Review", "Execute", "Analyze", "Summary", "Done"];
    for (const phase of phases) {
      expect(screen.getByText(phase)).toBeInTheDocument();
    }
  });

  it("shows iteration progress bar when iterations > 0", () => {
    render(<ProgressDisplay experiment={makeExperiment({ iteration_count: 3 })} />);
    expect(screen.getByText("Iterations")).toBeInTheDocument();
    expect(screen.getByText("3 / 5")).toBeInTheDocument();
  });

  it("hides iteration progress when iteration_count is 0", () => {
    render(<ProgressDisplay experiment={makeExperiment({ iteration_count: 0 })} />);
    expect(screen.queryByText("Iterations")).not.toBeInTheDocument();
  });

  it("renders completed status properly", () => {
    render(
      <ProgressDisplay
        experiment={makeExperiment({ status: "completed", phase: "done" })}
      />,
    );
    expect(screen.getByText("completed")).toBeInTheDocument();
  });
});
