# Feedback Components

Shared components for loading, empty, and error states. Used across all features to provide consistent visual feedback patterns.

## Components

### `LoadingSpinner`

Centered spinner with an optional text message. Uses the Lucide `Loader2` icon with a spin animation.

**Props:**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `message` | `string?` | `undefined` | Optional text displayed below the spinner |

**Usage:** Primary `Suspense` fallback in the app `Layout`, and used inline wherever async content loads.

### `EmptyState`

Centered placeholder for pages or sections with no data. Displays a large icon, title, description, and an optional action element (e.g. a button or link).

**Props:**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `icon` | `LucideIcon` | required | Large icon displayed above the title |
| `title` | `string` | required | Heading text |
| `description` | `string` | required | Supporting description text |
| `action` | `ReactNode?` | `undefined` | Optional CTA (button, link, etc.) |

### `ErrorBoundary`

React class component that catches rendering errors in its subtree. Displays a card with the error message and a "Try again" button that resets the error state. Accepts an optional `fallback` prop for custom error UI.

**Props:**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | required | Content to render |
| `fallback` | `ReactNode?` | `undefined` | Custom fallback UI (overrides the default error card) |

**Usage:** Wraps the `<Outlet>` in the app `Layout` to catch page-level errors. Also used per-tab in the Results page.

## Key Files

| File | Purpose |
|------|---------|
| `LoadingSpinner.tsx` | Spinner component with optional message |
| `LoadingSpinner.test.tsx` | Tests for spinner rendering |
| `EmptyState.tsx` | Empty data placeholder with icon, text, and action |
| `EmptyState.test.tsx` | Tests for empty state rendering |
| `ErrorBoundary.tsx` | React error boundary with retry capability |
