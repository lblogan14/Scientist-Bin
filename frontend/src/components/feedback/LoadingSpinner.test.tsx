import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { LoadingSpinner } from "./LoadingSpinner";

describe("LoadingSpinner", () => {
  it("renders a spinner SVG", () => {
    const { container } = render(<LoadingSpinner />);
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
    expect(svg).toHaveClass("animate-spin");
  });

  it("renders optional message when provided", () => {
    render(<LoadingSpinner message="Loading experiments..." />);
    expect(screen.getByText("Loading experiments...")).toBeInTheDocument();
  });

  it("does not render message when not provided", () => {
    const { container } = render(<LoadingSpinner />);
    const paragraphs = container.querySelectorAll("p");
    expect(paragraphs.length).toBe(0);
  });
});
