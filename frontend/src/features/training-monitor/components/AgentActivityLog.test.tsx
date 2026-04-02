import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { AgentActivityLog } from "./AgentActivityLog";
import type { AgentActivity } from "@/types/api";

describe("AgentActivityLog", () => {
  it("renders empty state when no activities", () => {
    render(<AgentActivityLog activities={[]} />);
    expect(screen.getByText("No agent activity recorded yet.")).toBeInTheDocument();
  });

  it("renders activity count", () => {
    const activities: AgentActivity[] = [
      { agent: "central", action: "phase_change", timestamp: "2026-04-01T10:00:00Z", details: "Started analysis" },
      { agent: "analyst", action: "completed", timestamp: "2026-04-01T10:01:00Z" },
    ];
    render(<AgentActivityLog activities={activities} />);
    expect(screen.getByText("(2)")).toBeInTheDocument();
  });

  it("renders activity action badges", () => {
    const activities: AgentActivity[] = [
      { agent: "central", action: "phase_change", timestamp: "2026-04-01T10:00:00Z" },
    ];
    render(<AgentActivityLog activities={activities} />);
    expect(screen.getByText("phase_change")).toBeInTheDocument();
  });

  it("renders activity details when present", () => {
    const activities: AgentActivity[] = [
      { agent: "plan", action: "research", timestamp: "2026-04-01T10:00:00Z", details: "Searching for best practices" },
    ];
    render(<AgentActivityLog activities={activities} />);
    expect(screen.getByText("Searching for best practices")).toBeInTheDocument();
  });
});
