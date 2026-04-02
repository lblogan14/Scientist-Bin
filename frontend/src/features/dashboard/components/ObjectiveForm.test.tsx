import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ObjectiveForm } from "./ObjectiveForm";

// Mock the submit hook
const mockMutate = vi.fn();
const mockClearError = vi.fn();

vi.mock("../hooks/use-submit-train", () => ({
  useSubmitTrain: () => ({
    mutate: mockMutate,
    isPending: false,
    errorMessage: null,
    clearError: mockClearError,
  }),
}));

function renderForm() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <MemoryRouter>
          <ObjectiveForm />
        </MemoryRouter>
      </TooltipProvider>
    </QueryClientProvider>,
  );
}

describe("ObjectiveForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the form fields", () => {
    renderForm();
    expect(screen.getByLabelText("Objective")).toBeInTheDocument();
    expect(screen.getByLabelText(/Data Description/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Dataset File Path/)).toBeInTheDocument();
    expect(screen.getByText("Launch Training")).toBeInTheDocument();
  });

  it("shows validation error when objective is too short", async () => {
    renderForm();
    const user = userEvent.setup();
    const textarea = screen.getByLabelText("Objective");
    await user.type(textarea, "short");
    fireEvent.submit(screen.getByText("Launch Training"));
    await waitFor(() => {
      expect(screen.getByText(/at least 10 characters/)).toBeInTheDocument();
    });
  });

  it("calls mutate with form data on valid submission", async () => {
    renderForm();
    const user = userEvent.setup();
    const textarea = screen.getByLabelText("Objective");
    await user.type(textarea, "Classify iris species from measurements");
    fireEvent.submit(screen.getByText("Launch Training"));
    await waitFor(() => {
      expect(mockMutate).toHaveBeenCalledWith(
        expect.objectContaining({
          objective: "Classify iris species from measurements",
        }),
      );
    });
  });

  it("renders auto-approve toggle", () => {
    renderForm();
    expect(screen.getByLabelText("Auto-approve plan")).toBeInTheDocument();
  });
});
