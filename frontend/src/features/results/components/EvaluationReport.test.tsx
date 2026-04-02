import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { EvaluationReport } from "./EvaluationReport";
import type { ExperimentRecord } from "@/types/api";

function makeRecord(overrides: Partial<ExperimentRecord> = {}): ExperimentRecord {
  return {
    iteration: 1,
    algorithm: "RandomForest",
    hyperparameters: {},
    metrics: { accuracy: 0.95, f1: 0.93 },
    training_time_seconds: 2.5,
    timestamp: "2026-04-01T00:00:00Z",
    ...overrides,
  };
}

describe("EvaluationReport", () => {
  it("returns null when evaluation is null and history is empty", () => {
    const { container } = render(
      <EvaluationReport evaluation={null} experimentHistory={[]} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("returns null when both props are undefined/null", () => {
    const { container } = render(
      <EvaluationReport evaluation={null} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders table with experiment history data", () => {
    const history = [
      makeRecord({ iteration: 1, algorithm: "RandomForest", metrics: { accuracy: 0.95 } }),
      makeRecord({ iteration: 2, algorithm: "SVC", metrics: { accuracy: 0.88 } }),
    ];
    render(
      <EvaluationReport evaluation={null} experimentHistory={history} />,
    );

    expect(screen.getByText("Experiment History")).toBeInTheDocument();
    expect(screen.getByText("RandomForest")).toBeInTheDocument();
    expect(screen.getByText("SVC")).toBeInTheDocument();
    expect(screen.getByText("0.9500")).toBeInTheDocument();
    expect(screen.getByText("0.8800")).toBeInTheDocument();
  });

  it("renders table headers for all unique metrics", () => {
    const history = [
      makeRecord({ metrics: { accuracy: 0.95, f1: 0.93 } }),
      makeRecord({ iteration: 2, metrics: { accuracy: 0.88, precision: 0.90 } }),
    ];
    render(
      <EvaluationReport evaluation={null} experimentHistory={history} />,
    );

    expect(screen.getByText("accuracy")).toBeInTheDocument();
    expect(screen.getByText("f1")).toBeInTheDocument();
    expect(screen.getByText("precision")).toBeInTheDocument();
  });

  it("shows Iter and Algorithm columns", () => {
    const history = [makeRecord()];
    render(
      <EvaluationReport evaluation={null} experimentHistory={history} />,
    );

    expect(screen.getByText("Iter")).toBeInTheDocument();
    expect(screen.getByText("Algorithm")).toBeInTheDocument();
    expect(screen.getByText("Time (s)")).toBeInTheDocument();
  });

  it("shows training time formatted to 1 decimal", () => {
    const history = [makeRecord({ training_time_seconds: 12.345 })];
    render(
      <EvaluationReport evaluation={null} experimentHistory={history} />,
    );

    expect(screen.getByText("12.3")).toBeInTheDocument();
  });

  it("marks best row when multiple records exist", () => {
    const history = [
      makeRecord({ iteration: 1, algorithm: "RF", metrics: { accuracy: 0.95 } }),
      makeRecord({ iteration: 2, algorithm: "SVC", metrics: { accuracy: 0.88 } }),
    ];
    render(
      <EvaluationReport evaluation={null} experimentHistory={history} />,
    );

    // The best row should have a "Best" badge
    expect(screen.getByText("Best")).toBeInTheDocument();
  });

  it("falls back to raw JSON when only evaluation object is provided", () => {
    const evaluation = { best_model: "RF", accuracy: 0.95 };
    render(
      <EvaluationReport evaluation={evaluation} experimentHistory={[]} />,
    );

    // Should render JSON in a pre element
    const pre = document.querySelector("pre");
    expect(pre).toBeInTheDocument();
    expect(pre!.textContent).toContain("RF");
  });
});
