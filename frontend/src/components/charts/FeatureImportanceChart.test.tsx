import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { FeatureImportanceChart } from "./FeatureImportanceChart";

const mockFeatures = [
  { feature: "petal_length", importance: 0.45 },
  { feature: "petal_width", importance: 0.35 },
  { feature: "sepal_length", importance: 0.12 },
  { feature: "sepal_width", importance: 0.08 },
];

describe("FeatureImportanceChart", () => {
  it("renders title with algorithm name", () => {
    render(
      <FeatureImportanceChart features={mockFeatures} algorithm="RandomForest" />,
    );
    expect(
      screen.getByText("Feature Importance — RandomForest"),
    ).toBeInTheDocument();
  });

  it("renders default title when no algorithm provided", () => {
    render(<FeatureImportanceChart features={mockFeatures} />);
    expect(screen.getByText("Feature Importance")).toBeInTheDocument();
  });

  it("renders the chart container", () => {
    const { container } = render(
      <FeatureImportanceChart features={mockFeatures} />,
    );
    expect(container.querySelector(".recharts-responsive-container")).toBeInTheDocument();
  });

  it("renders with maxFeatures limit without errors", () => {
    const { container } = render(
      <FeatureImportanceChart features={mockFeatures} maxFeatures={2} />,
    );
    expect(container.querySelector(".recharts-responsive-container")).toBeInTheDocument();
  });
});
