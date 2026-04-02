import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ConsoleOutput } from "./ConsoleOutput";

describe("ConsoleOutput", () => {
  it("renders waiting message when no logs", () => {
    render(<ConsoleOutput logs={[]} />);
    expect(screen.getByText("Waiting for output...")).toBeInTheDocument();
  });

  it("renders log line count", () => {
    render(<ConsoleOutput logs={["line 1", "line 2", "line 3"]} />);
    expect(screen.getByText("(3 lines)")).toBeInTheDocument();
  });

  it("renders log content", () => {
    render(<ConsoleOutput logs={["Training model...", "Accuracy: 0.95"]} />);
    expect(screen.getByText("Training model...")).toBeInTheDocument();
    expect(screen.getByText("Accuracy: 0.95")).toBeInTheDocument();
  });

  it("applies error styling to error lines", () => {
    render(<ConsoleOutput logs={["ImportError: No module named sklearn"]} />);
    const errorLine = screen.getByText("ImportError: No module named sklearn");
    expect(errorLine.className).toContain("text-destructive");
  });

  it("applies primary styling to METRIC: lines", () => {
    render(<ConsoleOutput logs={["METRIC: accuracy=0.95"]} />);
    const metricLine = screen.getByText("METRIC: accuracy=0.95");
    expect(metricLine.className).toContain("text-primary");
  });
});
