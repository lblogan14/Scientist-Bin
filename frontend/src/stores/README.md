# Stores

Client-side state management using [Zustand](https://github.com/pmndrs/zustand).

## app-store.ts

Global UI state store created with `create<AppState>()`. Three state slices:

### Sidebar

- `sidebarOpen: boolean` -- whether the sidebar is expanded
- `toggleSidebar()` -- toggles sidebar open/closed
- `setSidebarOpen(open)` -- sets sidebar state directly

### Theme

- `theme: Theme` -- current color scheme (`"light"`, `"dark"`, or `"science"`)
- `setTheme(theme)` -- applies the theme class on `<html>`, persists to `localStorage` key `scientist-bin-theme`

Initial theme is read from `localStorage` on store creation. The `applyTheme()` helper manages the `dark` / `science` CSS classes on `document.documentElement`.

### Selected Experiment

- `selectedExperimentId: string | null` -- the currently selected experiment ID, shared across pages
- `setSelectedExperimentId(id)` -- updates the selected experiment

This field enables cross-page experiment persistence. When a user selects an experiment on one page (e.g., Training Monitor), navigating to another page (e.g., Results) carries the selection over. The `useExperimentIdSync` hook (in `src/hooks/`) bridges this store value with the URL `?id=` query parameter.
