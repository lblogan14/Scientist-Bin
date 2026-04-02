import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { AnalysisTab } from "./AnalysisTab";

describe("AnalysisTab", () => {
  it("shows no-data message when report is null", () => {
    render(
      <AnalysisTab
        analysisReport={null}
        experimentId="exp-1"
      />,
    );
    expect(
      screen.getByText("No data analysis report available for this experiment."),
    ).toBeInTheDocument();
  });

  it("renders markdown content when report exists", () => {
    const report = ["## Data Profile", "", "The dataset has 150 samples."].join(
      "\n",
    );
    render(
      <AnalysisTab
        analysisReport={report}
        experimentId="exp-1"
      />,
    );
    expect(
      screen.getByRole("heading", { level: 2 }),
    ).toHaveTextContent("Data Profile");
    expect(
      screen.getByText("The dataset has 150 samples."),
    ).toBeInTheDocument();
  });

  it("shows download button when report exists", () => {
    render(
      <AnalysisTab
        analysisReport="Some report content"
        experimentId="exp-1"
      />,
    );
    expect(screen.getByText("Download Report")).toBeInTheDocument();
    const downloadLink = screen.getByText("Download Report").closest("a");
    expect(downloadLink).toHaveAttribute(
      "href",
      "/api/v1/experiments/exp-1/artifacts/analysis",
    );
  });

  it("shows split data paths when provided", () => {
    render(
      <AnalysisTab
        analysisReport="Report content"
        splitDataPaths={{
          train: "/data/runs/exp-1/data/train.csv",
          val: "/data/runs/exp-1/data/val.csv",
          test: "/data/runs/exp-1/data/test.csv",
        }}
        experimentId="exp-1"
      />,
    );
    expect(
      screen.getByText("Train / Validation / Test Split"),
    ).toBeInTheDocument();
    expect(screen.getByText(/train\.csv/)).toBeInTheDocument();
    expect(screen.getByText(/val\.csv/)).toBeInTheDocument();
    expect(screen.getByText(/test\.csv/)).toBeInTheDocument();
  });

  it("does not show split data section when paths are null", () => {
    render(
      <AnalysisTab
        analysisReport="Report"
        splitDataPaths={null}
        experimentId="exp-1"
      />,
    );
    expect(
      screen.queryByText("Train / Validation / Test Split"),
    ).not.toBeInTheDocument();
  });

  it("does not show split data section when paths are empty", () => {
    render(
      <AnalysisTab
        analysisReport="Report"
        splitDataPaths={{}}
        experimentId="exp-1"
      />,
    );
    expect(
      screen.queryByText("Train / Validation / Test Split"),
    ).not.toBeInTheDocument();
  });
});
