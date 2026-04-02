import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { FlaskConical, Search } from "lucide-react";
import { EmptyState } from "./EmptyState";

describe("EmptyState", () => {
  it("renders title and description", () => {
    render(
      <EmptyState
        icon={FlaskConical}
        title="No experiments"
        description="Launch your first experiment."
      />,
    );
    expect(screen.getByText("No experiments")).toBeInTheDocument();
    expect(
      screen.getByText("Launch your first experiment."),
    ).toBeInTheDocument();
  });

  it("renders the icon", () => {
    const { container } = render(
      <EmptyState
        icon={Search}
        title="No results"
        description="Try a different search."
      />,
    );
    // Lucide icons render as SVGs
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
  });

  it("renders optional action element", () => {
    render(
      <EmptyState
        icon={FlaskConical}
        title="Empty"
        description="Nothing here"
        action={<button>Create New</button>}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Create New" }),
    ).toBeInTheDocument();
  });

  it("does not render action when not provided", () => {
    render(
      <EmptyState
        icon={FlaskConical}
        title="Empty"
        description="Nothing here"
      />,
    );
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
