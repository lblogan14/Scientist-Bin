# Layout Components

Application shell components: sidebar navigation and header bar.

## Components

### `AppSidebar`

Left-side navigation using shadcn/ui `Sidebar` primitives. Includes five nav items:

| Route | Label | Icon |
|-------|-------|------|
| `/` | Dashboard | `LayoutDashboard` |
| `/experiments` | Experiments | `FlaskConical` |
| `/monitor` | Training | `Activity` |
| `/results` | Results | `BarChart3` |
| `/models` | Models | `Boxes` |

**Plan review notification:** The sidebar polls for experiments in the `plan_review` phase every 10 seconds. When any experiment is awaiting review, an amber pulsing dot appears next to the "Training" nav item, prompting the user to visit the Training Monitor page.

**Active state:** Nav items highlight based on the current URL pathname. The root path (`/`) uses exact matching; all others use prefix matching.

### `Header`

Top header bar with three elements:

1. **Sidebar toggle** -- `PanelLeft` icon button that collapses/expands the sidebar via `useSidebar()`.
2. **Health indicator** -- Polls `GET /api/v1/health` every 30 seconds. Shows a colored dot (green = healthy, red = unavailable, yellow = unknown) with a tooltip label.
3. **Theme switcher** -- Dropdown menu with three theme options:
   - **Light** (Sun icon)
   - **Dark** (Moon icon)
   - **Science** (FlaskConical icon)

   Theme state is managed by Zustand (`useAppStore`) and persisted to `localStorage`.

## Key Files

| File | Purpose |
|------|---------|
| `AppSidebar.tsx` | Navigation sidebar with plan-review notification polling |
| `Header.tsx` | Header bar with health indicator, sidebar toggle, and theme switcher |
| `Header.test.tsx` | Tests for Header component rendering and interactions |
