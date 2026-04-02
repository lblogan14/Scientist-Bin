import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SidebarProvider } from "@/components/ui/sidebar";
import { Header } from "./Header";

// Mock the health check API to avoid real requests
vi.mock("@/lib/api-client", () => ({
  checkHealth: vi.fn().mockResolvedValue({ status: "ok" }),
}));

// Stub window.matchMedia for useMobile hook used by SidebarProvider
beforeAll(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
});

function renderHeader() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <SidebarProvider>
          <Header />
        </SidebarProvider>
      </TooltipProvider>
    </QueryClientProvider>,
  );
}

describe("Header", () => {
  it("renders the header element", () => {
    renderHeader();
    expect(document.querySelector("header")).toBeInTheDocument();
  });

  it("renders health status text", () => {
    renderHeader();
    // Should show one of the health status messages
    const healthTexts = ["Backend healthy", "Backend status unknown", "Backend unavailable"];
    const found = healthTexts.some((text) => screen.queryByText(text));
    expect(found).toBe(true);
  });

  it("renders sidebar toggle and theme toggle buttons", () => {
    renderHeader();
    const buttons = document.querySelectorAll("header button");
    // Should have at least 2 buttons: sidebar toggle + theme toggle
    expect(buttons.length).toBeGreaterThanOrEqual(2);
  });
});
