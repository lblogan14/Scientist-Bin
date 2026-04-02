import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { CodeDisplay } from "./CodeDisplay";

// Mock the app store so useCodeTheme returns a valid theme
vi.mock("@/stores/app-store", () => ({
  useAppStore: (selector: (s: { theme: string }) => string) =>
    selector({ theme: "light" }),
}));

describe("CodeDisplay", () => {
  it("shows no-code message when code is null", () => {
    render(<CodeDisplay code={null} />);
    expect(screen.getByText("No code generated yet.")).toBeInTheDocument();
  });

  it("renders code with syntax highlighting", () => {
    const code = 'from sklearn.ensemble import RandomForestClassifier\nmodel = RandomForestClassifier()';
    render(<CodeDisplay code={code} />);
    expect(screen.getByText("Generated Code")).toBeInTheDocument();
    // The code should be rendered inside a pre element
    const pre = document.querySelector("pre");
    expect(pre).toBeInTheDocument();
    expect(pre!.textContent).toContain("RandomForestClassifier");
  });

  it("shows line numbers", () => {
    const code = 'import sklearn\nprint("hello")';
    render(<CodeDisplay code={code} />);
    // Line number 1 and 2 should appear
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });
});
