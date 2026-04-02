import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { SummaryTab } from "./SummaryTab";
import type { SummaryReportSections } from "@/types/api";

function makeSections(
  overrides: Partial<SummaryReportSections> = {},
): SummaryReportSections {
  return {
    title: "Experiment Summary",
    executive_summary: "",
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
    ...overrides,
  };
}

describe("SummaryTab", () => {
  it("shows no-data message when both summaryReport and sections are null", () => {
    render(
      <SummaryTab
        summaryReport={null}
        sections={null}
        experimentId="exp-1"
      />,
    );
    expect(
      screen.getByText("No summary report available for this experiment."),
    ).toBeInTheDocument();
  });

  it("shows no-data message when both are undefined", () => {
    render(<SummaryTab experimentId="exp-1" />);
    expect(
      screen.getByText("No summary report available for this experiment."),
    ).toBeInTheDocument();
  });

  it("renders accordion sections when reportSections provided", () => {
    const sections = makeSections({
      executive_summary: "Strong results were achieved.",
      methodology: "Random Forest with cross-validation.",
    });
    render(
      <SummaryTab
        sections={sections}
        experimentId="exp-1"
      />,
    );
    expect(screen.getByText("Experiment Summary")).toBeInTheDocument();
    expect(screen.getByText("Executive Summary")).toBeInTheDocument();
    expect(screen.getByText("Methodology")).toBeInTheDocument();
  });

  it("renders recommendations accordion trigger when provided", () => {
    const sections = makeSections({
      executive_summary: "Summary text",
      recommendations: ["Try more features", "Increase training data"],
    });
    render(
      <SummaryTab
        sections={sections}
        experimentId="exp-1"
      />,
    );
    // Recommendations section appears as an accordion trigger
    expect(screen.getByText("Recommendations")).toBeInTheDocument();
    // Content is inside a collapsed accordion panel, not visible by default
    // but it should be present in the DOM (hidden)
    const accordionItems = document.querySelectorAll(
      '[data-slot="accordion-item"]',
    );
    // Should have at least 2: executive_summary + recommendations
    expect(accordionItems.length).toBeGreaterThanOrEqual(2);
  });

  it("falls back to markdown when no sections provided", () => {
    const report = ["## Summary", "", "Here are the results."].join("\n");
    render(
      <SummaryTab
        summaryReport={report}
        sections={null}
        experimentId="exp-1"
      />,
    );
    expect(
      screen.getByRole("heading", { level: 2 }),
    ).toHaveTextContent("Summary");
    expect(screen.getByText("Here are the results.")).toBeInTheDocument();
  });

  it("shows download button", () => {
    render(
      <SummaryTab
        summaryReport="Some report"
        experimentId="exp-42"
      />,
    );
    expect(screen.getByText("Download Report")).toBeInTheDocument();
    const link = screen.getByText("Download Report").closest("a");
    expect(link).toHaveAttribute(
      "href",
      "/api/v1/experiments/exp-42/artifacts/summary",
    );
  });

  it("skips accordion sections with empty content", () => {
    const sections = makeSections({
      executive_summary: "Summary here",
      methodology: "",
      conclusions: "   ",
    });
    render(
      <SummaryTab
        sections={sections}
        experimentId="exp-1"
      />,
    );
    expect(screen.getByText("Executive Summary")).toBeInTheDocument();
    // Empty methodology and whitespace conclusions should be skipped
    expect(screen.queryByText("Methodology")).not.toBeInTheDocument();
    expect(screen.queryByText("Conclusions")).not.toBeInTheDocument();
  });

  it("prefers sections over summaryReport when both are provided", () => {
    const sections = makeSections({
      title: "Structured Report",
      executive_summary: "Structured summary",
    });
    render(
      <SummaryTab
        summaryReport="# Markdown Report"
        sections={sections}
        experimentId="exp-1"
      />,
    );
    // Should use sections (accordion) view
    expect(screen.getByText("Structured Report")).toBeInTheDocument();
    expect(screen.getByText("Executive Summary")).toBeInTheDocument();
  });
});
