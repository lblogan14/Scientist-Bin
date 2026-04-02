import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { GroupedBarChart } from "./GroupedBarChart";

describe("GroupedBarChart", () => {
  it("renders null when data is empty", () => {
    const { container } = render(
      <GroupedBarChart title="Test" data={[]} xKey="name" yKeys={["value"]} />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders null when data is undefined", () => {
    const { container } = render(
      <GroupedBarChart
        title="Test"
        data={undefined as unknown as Record<string, unknown>[]}
        xKey="name"
        yKeys={["value"]}
      />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders the title when data is present", () => {
    const data = [{ name: "RF", accuracy: 0.95 }];
    render(
      <GroupedBarChart
        title="Algorithm Comparison"
        data={data}
        xKey="name"
        yKeys={["accuracy"]}
      />,
    );
    expect(screen.getByText("Algorithm Comparison")).toBeInTheDocument();
  });
});
