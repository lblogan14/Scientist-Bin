import { render, screen } from "@testing-library/react";
import { ConfusionMatrixHeatmap } from "./ConfusionMatrixHeatmap";

describe("ConfusionMatrixHeatmap", () => {
  const labels = ["cat", "dog", "bird"];
  const matrix = [
    [10, 1, 0],
    [2, 8, 1],
    [0, 0, 9],
  ];

  it("renders the title", () => {
    render(
      <ConfusionMatrixHeatmap
        labels={labels}
        matrix={matrix}
        title="Test CM"
      />,
    );
    expect(screen.getByText("Test CM")).toBeInTheDocument();
  });

  it("renders all class labels as column headers", () => {
    render(<ConfusionMatrixHeatmap labels={labels} matrix={matrix} />);
    // Each label appears twice: once as column header, once as row header
    expect(screen.getAllByText("cat")).toHaveLength(2);
    expect(screen.getAllByText("dog")).toHaveLength(2);
    expect(screen.getAllByText("bird")).toHaveLength(2);
  });

  it("renders all cell values", () => {
    render(<ConfusionMatrixHeatmap labels={labels} matrix={matrix} />);
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();
    expect(screen.getByText("9")).toBeInTheDocument();
  });

  it("renders axis labels", () => {
    render(<ConfusionMatrixHeatmap labels={labels} matrix={matrix} />);
    expect(screen.getByText("Predicted")).toBeInTheDocument();
    expect(screen.getByText("Actual")).toBeInTheDocument();
  });

  it("uses default title when none provided", () => {
    render(<ConfusionMatrixHeatmap labels={labels} matrix={matrix} />);
    expect(screen.getByText("Confusion Matrix")).toBeInTheDocument();
  });
});
