# Hooks

Shared React hooks used across multiple features.

## use-experiment-id-sync.ts

Bridges the URL `?id=` query parameter with the Zustand `selectedExperimentId` store value. Used by Training Monitor, Results, and Model Selection pages to maintain a consistent experiment selection across navigation.

**Sync rules:**

1. **URL wins on load** -- if the URL has `?id=abc`, the store is updated to `abc`
2. **Store fills empty URLs** -- if the URL has no `?id=` but the store has a value, the URL is updated (with `replace: true` to avoid polluting history)
3. **Setter updates both** -- `setExperimentId(id)` writes to both the store and the URL simultaneously

**Return value:** `{ experimentId, setExperimentId }`

- `experimentId` -- resolved value (`urlId ?? storeId`)
- `setExperimentId(id)` -- callback that sets both the Zustand store and URL search params

## use-css-vars.ts

Utility hook for reading CSS custom property values.

## use-mobile.ts

Responsive breakpoint hook for detecting mobile viewports.
