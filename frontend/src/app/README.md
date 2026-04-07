# App

Application entry point, routing, providers, and shell layout.

## Files

| File | Purpose |
|------|---------|
| `App.tsx` | Root component: wraps `RouterProvider` inside `Providers` |
| `router.tsx` | Route definitions using React Router v7 `createBrowserRouter` |
| `providers.tsx` | Global providers: `QueryClientProvider` (TanStack React Query) and `TooltipProvider` (shadcn/ui) |
| `Layout.tsx` | Shell layout: sidebar + header + `<Outlet>` with `ErrorBoundary` and `Suspense` wrappers |

## Routes

All page components are lazy-loaded via `React.lazy()` for code splitting.

| Path | Feature | Page Component |
|------|---------|----------------|
| `/` | Dashboard | `DashboardPage` |
| `/experiments` | Experiment Setup | `ExperimentSetupPage` |
| `/monitor` | Training Monitor | `TrainingMonitorPage` |
| `/results` | Results | `ResultsPage` |
| `/results/:id` | Results (deep link) | `ResultsPage` |
| `/models` | Model Selection | `ModelSelectionPage` |
| `*` | Catch-all | Redirects to `/` |

## Layout Structure

```
SidebarProvider
  -> skip-to-content link (accessibility)
  -> AppSidebar (left nav)
  -> Header (health indicator, theme switcher, sidebar toggle)
  -> <main>
       -> ErrorBoundary
            -> Suspense (LoadingSpinner fallback)
                 -> Outlet (page content)
```

## Query Client Configuration

- `staleTime`: 30 seconds
- `refetchOnWindowFocus`: enabled
- `retry`: 1 attempt

## Conventions

- All routes are wrapped in the shared `Layout` shell -- no full-page routes exist outside it.
- Page-level code splitting ensures only the active page bundle is loaded.
- The `@/` path alias maps to `src/` (configured in `tsconfig.json`).
