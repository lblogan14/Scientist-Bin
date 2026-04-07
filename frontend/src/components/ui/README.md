# UI Primitives (shadcn/ui)

Auto-generated shadcn/ui components based on Radix UI and Tailwind CSS v4. These are **owned source files** committed to the repo (not installed from `node_modules`).

## Conventions

- **ESLint-ignored:** This directory is excluded from ESLint checks since the components are generated code.
- **Do not edit manually** unless customizing a specific component's behavior. Prefer extending via wrapper components in `components/shared/` or `components/layout/`.
- **Adding new components:** Use `pnpm dlx shadcn@latest add <component>` from the `frontend/` directory. The CLI writes the component file here automatically.
- **Styling:** Components use CSS variables from `src/index.css` for theming (`:root`, `.dark`, `.science` scopes). Colors reference `hsl(var(--...))` tokens.

## Available Components

| Component | File | Radix Primitive |
|-----------|------|-----------------|
| Accordion | `accordion.tsx` | `@radix-ui/react-accordion` |
| Alert | `alert.tsx` | -- (styled `div`) |
| Badge | `badge.tsx` | -- (styled `span`) |
| Button | `button.tsx` | `@radix-ui/react-slot` |
| Card | `card.tsx` | -- (styled `div`) |
| Dialog | `dialog.tsx` | `@radix-ui/react-dialog` |
| Dropdown Menu | `dropdown-menu.tsx` | `@radix-ui/react-dropdown-menu` |
| Input | `input.tsx` | -- (styled `input`) |
| Label | `label.tsx` | `@radix-ui/react-label` |
| Scroll Area | `scroll-area.tsx` | `@radix-ui/react-scroll-area` |
| Select | `select.tsx` | `@radix-ui/react-select` |
| Separator | `separator.tsx` | `@radix-ui/react-separator` |
| Sheet | `sheet.tsx` | `@radix-ui/react-dialog` |
| Sidebar | `sidebar.tsx` | -- (custom composite) |
| Skeleton | `skeleton.tsx` | -- (styled `div`) |
| Switch | `switch.tsx` | `@radix-ui/react-switch` |
| Table | `table.tsx` | -- (styled `table`) |
| Tabs | `tabs.tsx` | `@radix-ui/react-tabs` |
| Textarea | `textarea.tsx` | -- (styled `textarea`) |
| Tooltip | `tooltip.tsx` | `@radix-ui/react-tooltip` |

## Usage Pattern

Import from `@/components/ui/<component>`:

```tsx
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
```

All components support standard HTML attributes and a `className` prop for Tailwind overrides via the `cn()` utility.
