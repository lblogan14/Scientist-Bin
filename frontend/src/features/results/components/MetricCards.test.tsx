import { render, screen } from "@testing-library/react";
import { MetricCards } from "./MetricCards";

describe("MetricCards", () => {
  it("renders nothing when metrics is null", () => {
    const { container } = render(<MetricCards metrics={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing when metrics is empty", () => {
    const { container } = render(<MetricCards metrics={{}} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders a card for each metric", () => {
    const metrics = {
      accuracy: 0.95,
      f1: 0.92,
      loss: 0.15,
    };
    render(<MetricCards metrics={metrics} />);
    expect(screen.getByText("accuracy")).toBeInTheDocument();
    expect(screen.getByText("f1")).toBeInTheDocument();
    expect(screen.getByText("loss")).toBeInTheDocument();
  });

  it("formats numeric values to 4 decimal places", () => {
    render(<MetricCards metrics={{ accuracy: 0.9512345 }} />);
    expect(screen.getByText("0.9512")).toBeInTheDocument();
  });

  it("renders progress bar for ratio metrics", () => {
    const { container } = render(
      <MetricCards metrics={{ accuracy: 0.95 }} />,
    );
    // Should have a progress bar div
    const bars = container.querySelectorAll(".bg-green-500");
    expect(bars.length).toBeGreaterThan(0);
  });

  it("applies green color for metrics >= 0.9", () => {
    render(<MetricCards metrics={{ accuracy: 0.95 }} />);
    const valueEl = screen.getByText("0.9500");
    expect(valueEl).toHaveClass("text-green-600");
  });

  it("applies yellow color for metrics >= 0.7 and < 0.9", () => {
    render(<MetricCards metrics={{ accuracy: 0.75 }} />);
    const valueEl = screen.getByText("0.7500");
    expect(valueEl).toHaveClass("text-yellow-600");
  });

  it("handles non-numeric values gracefully", () => {
    render(<MetricCards metrics={{ model: "LogisticRegression" as unknown }} />);
    expect(screen.getByText("LogisticRegression")).toBeInTheDocument();
  });
});
