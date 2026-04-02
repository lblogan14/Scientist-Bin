import { isExperimentError } from "./api";
import type { ExperimentError, ExperimentResult } from "./api";

describe("isExperimentError", () => {
  it("returns true for an ExperimentError object", () => {
    const err: ExperimentError = { error: "Something failed" };
    expect(isExperimentError(err)).toBe(true);
  });

  it("returns true for an error with traceback", () => {
    const err: ExperimentError = {
      error: "Crash",
      traceback: "Traceback ...",
    };
    expect(isExperimentError(err)).toBe(true);
  });

  it("returns false for null", () => {
    expect(isExperimentError(null)).toBe(false);
  });

  it("returns false for a successful ExperimentResult", () => {
    const result: ExperimentResult = {
      framework: "sklearn",
      plan: null,
      plan_markdown: null,
      generated_code: null,
      evaluation_results: null,
      experiment_history: [],
      data_profile: null,
      problem_type: null,
      iterations: 0,
      analysis_report: null,
      summary_report: null,
      best_model: null,
      best_hyperparameters: null,
      test_metrics: null,
      test_diagnostics: null,
      selection_reasoning: null,
      report_sections: null,
      status: "completed",
    };
    expect(isExperimentError(result)).toBe(false);
  });
});
