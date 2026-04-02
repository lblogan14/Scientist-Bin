import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MetricLineChart } from "./MetricLineChart";

describe("MetricLineChart", () => {
  it("returns null when data is empty", () => {
    const { container } = render(
      <MetricLineChart title="Test" data={[]} xKey="step" yKey="value" />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("returns null when data is undefined", () => {
    const { container } = render(
      <MetricLineChart
        title="Test"
        data={undefined as unknown as Record<string, unknown>[]}
        xKey="step"
        yKey="value"
      />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders the title when data is present", () => {
    const data = [
      { step: 1, value: 0.5 },
      { step: 2, value: 0.7 },
    ];
    render(
      <MetricLineChart title="Accuracy Over Time" data={data} xKey="step" yKey="value" />,
    );
    expect(screen.getByText("Accuracy Over Time")).toBeInTheDocument();
  });
});
