import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { OverfitGaugeChart } from "./OverfitGaugeChart";
import type { OverfitEntry } from "@/types/api";

const mockEntries: OverfitEntry[] = [
  {
    algorithm: "RandomForest",
    metric_name: "accuracy",
    train_value: 0.98,
    val_value: 0.93,
    gap: 0.05,
    gap_percentage: 5.1,
    overfit_risk: "low",
  },
  {
    algorithm: "DecisionTree",
    metric_name: "accuracy",
    train_value: 1.0,
    val_value: 0.85,
    gap: 0.15,
    gap_percentage: 15.0,
    overfit_risk: "high",
  },
];

describe("OverfitGaugeChart", () => {
  it("renders the default title", () => {
    render(<OverfitGaugeChart entries={mockEntries} />);
    expect(screen.getByText("Overfitting Analysis")).toBeInTheDocument();
  });

  it("renders a custom title", () => {
    render(<OverfitGaugeChart entries={mockEntries} title="Overfit Check" />);
    expect(screen.getByText("Overfit Check")).toBeInTheDocument();
  });

  it("renders the chart container", () => {
    const { container } = render(<OverfitGaugeChart entries={mockEntries} />);
    expect(container.querySelector(".recharts-responsive-container")).toBeInTheDocument();
  });
});
