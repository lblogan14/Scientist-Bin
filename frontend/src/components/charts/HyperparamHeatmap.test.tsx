import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { HyperparamHeatmap } from "./HyperparamHeatmap";
import type { CVResultEntry } from "@/types/api";

const mockData: CVResultEntry[] = [
  { params: { n_estimators: 100, max_depth: 5 }, mean_score: 0.95, std_score: 0.02, rank: 1 },
  { params: { n_estimators: 200, max_depth: 10 }, mean_score: 0.93, std_score: 0.03, rank: 2 },
  { params: { n_estimators: 50, max_depth: 3 }, mean_score: 0.88, std_score: 0.05, rank: 3 },
];

describe("HyperparamHeatmap", () => {
  it("renders null when data is empty", () => {
    const { container } = render(<HyperparamHeatmap data={[]} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders the default title", () => {
    render(<HyperparamHeatmap data={mockData} />);
    expect(screen.getByText("Hyperparameter Search Results")).toBeInTheDocument();
  });

  it("renders param column headers", () => {
    render(<HyperparamHeatmap data={mockData} />);
    expect(screen.getByText("n_estimators")).toBeInTheDocument();
    expect(screen.getByText("max_depth")).toBeInTheDocument();
  });

  it("renders rank column and values", () => {
    render(<HyperparamHeatmap data={mockData} />);
    expect(screen.getByText("Rank")).toBeInTheDocument();
    // Ranks 1, 2, 3 are rendered in table cells
    const cells = screen.getAllByRole("cell");
    const rankTexts = cells.map((c) => c.textContent);
    expect(rankTexts).toContain("1");
    expect(rankTexts).toContain("2");
    expect(rankTexts).toContain("3");
  });

  it("renders mean score and std columns", () => {
    render(<HyperparamHeatmap data={mockData} />);
    expect(screen.getByText("Mean Score")).toBeInTheDocument();
    expect(screen.getByText("Std")).toBeInTheDocument();
    expect(screen.getByText("0.9500")).toBeInTheDocument();
    expect(screen.getByText("0.0200")).toBeInTheDocument();
  });
});
