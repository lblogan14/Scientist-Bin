import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { BoxPlotChart } from "./BoxPlotChart";

const mockData = [
  { name: "RandomForest", scores: [0.92, 0.94, 0.91, 0.93, 0.95], mean: 0.93 },
  { name: "GradientBoosting", scores: [0.89, 0.91, 0.88, 0.9, 0.92], mean: 0.9 },
];

describe("BoxPlotChart", () => {
  it("renders the default title", () => {
    render(<BoxPlotChart data={mockData} />);
    expect(screen.getByText("CV Fold Distribution")).toBeInTheDocument();
  });

  it("renders a custom title", () => {
    render(<BoxPlotChart data={mockData} title="Custom Title" />);
    expect(screen.getByText("Custom Title")).toBeInTheDocument();
  });

  it("renders algorithm names in the stats table", () => {
    render(<BoxPlotChart data={mockData} />);
    expect(screen.getByText("RandomForest")).toBeInTheDocument();
    expect(screen.getByText("GradientBoosting")).toBeInTheDocument();
  });

  it("renders stats table headers", () => {
    render(<BoxPlotChart data={mockData} />);
    expect(screen.getByText("Algorithm")).toBeInTheDocument();
    expect(screen.getByText("Min")).toBeInTheDocument();
    expect(screen.getByText("Max")).toBeInTheDocument();
    expect(screen.getByText("Mean")).toBeInTheDocument();
    expect(screen.getByText("Median")).toBeInTheDocument();
  });

  it("renders the responsive chart container", () => {
    const { container } = render(<BoxPlotChart data={mockData} />);
    expect(container.querySelector(".recharts-responsive-container")).toBeInTheDocument();
  });
});
