import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MemoryRouter } from "react-router";
import { RecentExperiments } from "./RecentExperiments";
import type { Experiment } from "@/types/api";

// Mock the useExperiments hook
const mockUseExperiments = vi.fn();
vi.mock("../hooks/use-experiments", () => ({
  useExperiments: () => mockUseExperiments(),
}));

function makeExperiment(overrides: Partial<Experiment> = {}): Experiment {
  return {
    id: "exp-1",
    objective: "Classify iris",
    data_description: "",
    data_file_path: null,
    framework: "sklearn",
    status: "completed",
    phase: "done",
    runs: [],
    best_run_id: null,
    iteration_count: 3,
    progress_events: [],
    result: null,
    execution_plan: null,
    analysis_report: null,
    summary_report: null,
    split_data_paths: null,
    created_at: "2026-04-01T00:00:00Z",
    updated_at: "2026-04-01T00:00:00Z",
    ...overrides,
  };
}

function renderWithRouter(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe("RecentExperiments", () => {
  it("renders skeleton when loading", () => {
    mockUseExperiments.mockReturnValue({ data: undefined, isLoading: true });
    const { container } = renderWithRouter(<RecentExperiments />);
    // Skeleton component uses data-slot="skeleton"
    const skeletons = container.querySelectorAll('[data-slot="skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("renders empty state when experiments is empty", () => {
    mockUseExperiments.mockReturnValue({ data: [], isLoading: false });
    renderWithRouter(<RecentExperiments />);
    expect(screen.getByText("No experiments yet")).toBeInTheDocument();
    expect(
      screen.getByText("Launch your first training experiment above."),
    ).toBeInTheDocument();
  });

  it("renders experiment list", () => {
    const experiments = [
      makeExperiment({ id: "1", objective: "Classify iris species" }),
      makeExperiment({
        id: "2",
        objective: "Predict house prices",
        status: "running",
        phase: "execution",
      }),
    ];
    mockUseExperiments.mockReturnValue({ data: experiments, isLoading: false });

    renderWithRouter(<RecentExperiments />);

    expect(screen.getByText("Recent Experiments")).toBeInTheDocument();
    expect(screen.getByText("Classify iris species")).toBeInTheDocument();
    expect(screen.getByText("Predict house prices")).toBeInTheDocument();
  });

  it("shows at most 5 experiments", () => {
    const experiments = Array.from({ length: 8 }, (_, i) =>
      makeExperiment({ id: `exp-${i}`, objective: `Experiment ${i}` }),
    );
    mockUseExperiments.mockReturnValue({ data: experiments, isLoading: false });

    renderWithRouter(<RecentExperiments />);

    // Only first 5 should render
    expect(screen.getByText("Experiment 0")).toBeInTheDocument();
    expect(screen.getByText("Experiment 4")).toBeInTheDocument();
    expect(screen.queryByText("Experiment 5")).not.toBeInTheDocument();
  });

  it("shows status badges", () => {
    const experiments = [
      makeExperiment({ id: "1", status: "completed" }),
      makeExperiment({ id: "2", status: "running" }),
    ];
    mockUseExperiments.mockReturnValue({ data: experiments, isLoading: false });

    renderWithRouter(<RecentExperiments />);

    expect(screen.getByText("completed")).toBeInTheDocument();
    expect(screen.getByText("running")).toBeInTheDocument();
  });

  it("shows phase badge for non-done experiments", () => {
    const experiments = [
      makeExperiment({ id: "1", status: "running", phase: "execution" }),
    ];
    mockUseExperiments.mockReturnValue({ data: experiments, isLoading: false });

    renderWithRouter(<RecentExperiments />);

    expect(screen.getByText("execution")).toBeInTheDocument();
  });

  it("shows iteration count when > 0", () => {
    const experiments = [
      makeExperiment({ id: "1", iteration_count: 5 }),
    ];
    mockUseExperiments.mockReturnValue({ data: experiments, isLoading: false });

    renderWithRouter(<RecentExperiments />);

    expect(screen.getByText("5 iter")).toBeInTheDocument();
  });

  it("links completed experiments to results page", () => {
    const experiments = [
      makeExperiment({ id: "abc", status: "completed" }),
    ];
    mockUseExperiments.mockReturnValue({ data: experiments, isLoading: false });

    renderWithRouter(<RecentExperiments />);

    const link = screen.getByText("Classify iris").closest("a");
    expect(link).toHaveAttribute("href", "/results?id=abc");
  });

  it("links running experiments to monitor page", () => {
    const experiments = [
      makeExperiment({ id: "xyz", status: "running" }),
    ];
    mockUseExperiments.mockReturnValue({ data: experiments, isLoading: false });

    renderWithRouter(<RecentExperiments />);

    const link = screen.getByText("Classify iris").closest("a");
    expect(link).toHaveAttribute("href", "/monitor?id=xyz");
  });
});
