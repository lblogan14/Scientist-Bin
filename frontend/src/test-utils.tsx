import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, type RenderOptions } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { TooltipProvider } from "@/components/ui/tooltip";

interface WrapperOptions {
  route?: string;
}

function createWrapper({ route = "/" }: WrapperOptions = {}) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <MemoryRouter initialEntries={[route]}>{children}</MemoryRouter>
        </TooltipProvider>
      </QueryClientProvider>
    );
  };
}

export function renderWithProviders(
  ui: React.ReactElement,
  options?: WrapperOptions & Omit<RenderOptions, "wrapper">,
) {
  const { route, ...renderOptions } = options ?? {};
  return render(ui, {
    wrapper: createWrapper({ route }),
    ...renderOptions,
  });
}
