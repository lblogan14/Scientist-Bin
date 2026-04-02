import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ConfusionMatrixTab } from "./ConfusionMatrixTab";

describe("ConfusionMatrixTab", () => {
  it("shows no-data message when no matrices are available", () => {
    render(<ConfusionMatrixTab />);
    expect(
      screen.getByText("No confusion matrix data available for this experiment."),
    ).toBeInTheDocument();
  });

  it("renders confusion matrix from matrices prop", () => {
    const matrices = {
      RandomForest: {
        labels: ["cat", "dog"],
        matrix: [
          [10, 2],
          [1, 12],
        ],
      },
    };
    render(<ConfusionMatrixTab matrices={matrices} />);
    expect(screen.getByText("Confusion Matrix — RandomForest")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
  });

  it("renders from experiment history fallback", () => {
    const history = [
      {
        iteration: 1,
        algorithm: "SVM",
        hyperparameters: {},
        metrics: { accuracy: 0.9 },
        training_time_seconds: 5,
        timestamp: "2026-04-01T10:00:00Z",
        confusion_matrix: {
          labels: ["A", "B"],
          matrix: [
            [8, 1],
            [2, 9],
          ],
        },
      },
    ];
    render(<ConfusionMatrixTab history={history} />);
    expect(screen.getByText("Confusion Matrix — SVM")).toBeInTheDocument();
  });
});
