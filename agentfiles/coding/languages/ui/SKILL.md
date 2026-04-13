---
name: ui-expert
description: >
  Use when building, iterating on, or reviewing UI — React components, Tailwind
  styling, shadcn/ui primitives, responsive layouts, design alternatives, or
  visual verification of what the browser actually renders. Covers two phases:
  (1) design specification — produce a structured component spec using visual
  mockups and the preview server for iteration; (2) implementation handoff —
  scaffold the project environment and produce a spec block that typescript-expert
  consumes to write the actual components. ui-expert owns what things should look
  like; typescript-expert owns the code. Also use for screenshot verification.
---

# UI Expert

Design intelligence for the React + Tailwind + shadcn/ui stack. Specifies what
things should look like, sets up the environment, then hands off to
`typescript-expert` for implementation. Visual iteration via a local preview
server. Screenshot verification so Claude can see what the browser actually renders.

## Stack

**Default:** React + TypeScript + Tailwind CSS + shadcn/ui

This is the most AI-capable frontend stack — widest training data, fewest
hallucinations, best component ecosystem. Use it unless the project already
has a different framework.

## Design Intelligence

Core design knowledge that separates good specs from generic ones. These are the
rules AI most commonly violates — apply them before writing any component spec.

### Token Architecture — Three Tiers

Never use raw hex values in a spec. Always use the three-tier hierarchy:

```
Primitive  →  --blue-500: #3B82F6
Semantic   →  --color-interactive: var(--blue-500)
Component  →  --button-bg: var(--color-interactive)
```

In Tailwind + shadcn, this means component specs reference CSS variable names:
- `bg-primary text-primary-foreground` — not `bg-blue-600 text-white`
- `bg-muted text-muted-foreground` — not `bg-gray-100 text-gray-500`
- `border-border` — not `border-zinc-200`
- `bg-destructive text-destructive-foreground` — for errors/danger

Semantic roles: `background`, `foreground`, `primary`, `secondary`, `muted`,
`accent`, `destructive`, `border`, `ring`, `input`, `card`, `popover`.

### Typography — Per-Level Rules

Apply line-height and letter-spacing by type level, not globally.

| Level | Size | line-height | letter-spacing | Tailwind |
|-------|------|-------------|----------------|---------|
| Display | >32px | 1.1–1.2 | -0.02em to -0.04em | `leading-tight tracking-tighter` |
| Heading | 20–32px | 1.2–1.3 | -0.01em to -0.02em | `leading-snug tracking-tight` |
| Body | 15–18px | 1.5–1.6 | 0 | `leading-relaxed` |
| UI label | 13–14px | 1.25 | 0 | `leading-none` (padding controls height) |
| Caption | ≤12px | 1.4 | +0.01em | `leading-normal tracking-wide` |
| Uppercase label | any | — | +0.05em to +0.1em | `uppercase tracking-widest` |

**What AI gets wrong:** Applying `leading-relaxed` to headings — large text needs
tight leading or it looks broken. Each ramp level needs its own value.

### Spacing — 8pt Grid + Internal ≤ External

All spacing is multiples of 8px. The 4px half-step exists only for icon gaps and
tight inline nudges, not general layout.

**Internal ≤ External rule (Gestalt proximity):** The padding *inside* a group must
not exceed the gap *between* groups, or items appear unrelated to their container.

```
Button:  px-4 py-2 (16/8px internal)   gap-3 (12px) between buttons  ✓
Card:    p-6 (24px internal)            gap-4 (16px) between cards    ✗ — gap should be ≥24px
Section: p-8–p-12 internal             mt-16–mt-24 between sections  ✓
```

### Color — Dark Mode Done Right

Dark mode is not `filter: invert()`. Three rules:

1. **No pure white text** — `#E0E0E0–#F0F0F0`, never `#FFFFFF` on dark surfaces
2. **Surface hierarchy via luminance, not shadows** — shadows disappear on dark.
   Use 4 luminance steps: `zinc-950 → zinc-900 → zinc-800 → zinc-700`
3. **Brand/accent colors need a lighter variant in dark mode** — e.g., `blue-600`
   in light → `blue-400` in dark. Same hex looks washed out. Increase luminance
   +10–20% and saturation slightly.

**State overlays (Material Design model):** Hover = 8% overlay, focus = 12%,
active = 12%, dragged = 16%. In Tailwind: `hover:bg-primary/90` or
`hover:opacity-90`.

**No indigo or blue by default** — they produce the generic SaaS look. Require
an explicit brand color decision. Gray-based neutrals (`zinc`, `slate`) are the
safe default for surfaces.

### State Matrix — Every Interactive Component

Spec all of these before handing off to typescript-expert. Missing states are
the most common cause of revision cycles.

| State | Notes | Commonly missed |
|-------|-------|----------------|
| Default | Base appearance | — |
| Hover | 8% overlay or explicit class | — |
| Focus-visible | Keyboard only — use `:focus-visible`, never remove rings | Usually forgotten |
| Active/pressed | 12% overlay, slight scale-down | Often skipped |
| Disabled | `opacity-50 pointer-events-none cursor-not-allowed` | — |
| Loading | Skeleton (layout preserved) or spinner (unknown duration) | Skeleton vs spinner conflated |
| Error/invalid | `border-destructive text-destructive` | — |
| Empty (new user) | CTA + onboarding prompt | Treated same as zero-results |
| Empty (zero results) | "Relax filters" prompt | Treated same as new-user empty |
| Read-only | Visible + copyable, not editable — NOT the same as disabled | Almost always missing |
| Indeterminate | Checkboxes in trees/tables need it | Almost always missing |
| Selected/active | For nav items, tabs, toggles | — |

### Semantic HTML First

Never div soup. Use structural elements — the spec should name them:
- `<main>`, `<header>`, `<nav>`, `<aside>`, `<section>`, `<article>`, `<footer>`
- `<button>` not `<div onclick>` — keyboard and a11y come for free
- `<label>` associated with inputs, always
- `sr-only` for screen-reader text — never `display:none` for accessible content
- Touch targets ≥ 44px on all interactive elements

---

## Workflow Overview

```
Phase 1 — Specify   →  Phase 2 — Environment   →  Phase 3 — Handoff   →  Phase 4 — Verify
Visual exploration      Scaffold or check           Component Spec          Screenshot after
Preview server          project setup               for typescript-expert   implementation
Design tokens           (Next.js + shadcn)          TypeScript interfaces
Component states        Quick, ui-expert owns       States, tokens, a11y
```

---

## Phase 1 — Design Specification

Before any code, produce a **Component Spec**. This is the design intelligence
phase — what should this look like, how should it behave, what states exist?

### 1a — Visual Exploration (use when choices are needed)

When the user needs to choose between design options, use the preview server to
show rendered options — visual beats verbal every time.

```bash
# Start preview server
af preview /tmp/ui-preview/
# Write HTML option files to /tmp/ui-preview/option-a.html etc.
# Server auto-refreshes; reads clicks from /tmp/ui-preview/events.jsonl
```

Write self-contained HTML mockups (Tailwind via CDN, no build step):

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.tailwindcss.com"></script>
  <title>Option A — Side Menu</title>
</head>
<body class="flex h-screen bg-zinc-50">
  <!-- layout mockup -->
</body>
</html>
```

### 1b — Produce Component Spec

Output a **COMPONENT SPEC** block. This is the contract between ui-expert
and typescript-expert. Be precise — exact token names and values, not prose.

```
## COMPONENT SPEC: <ComponentName>

### Design Tokens
- Colors: bg-zinc-950, text-zinc-50, border-zinc-800, accent: bg-blue-600
- Typography: heading font-semibold text-xl tracking-tight, body text-sm text-zinc-400
- Spacing: container px-6 py-4, gap-3 between items, mt-8 section spacing
- Radius: rounded-lg (cards), rounded-md (buttons), rounded-full (badges)
- Shadow: shadow-sm (cards), no shadow (buttons — rely on border instead)

### Layout
- Mobile: single column, stacked nav at bottom
- Tablet (md:): side nav 240px, content flex-1
- Desktop (lg:): side nav 280px, max-w-7xl container

### shadcn/ui Components
- Sheet — mobile nav drawer (side="left")
- Card + CardHeader + CardContent — data panels
- Button variant="outline" — secondary actions
- Badge variant="secondary" — status labels
- (Do NOT use: DropdownMenu for this — use plain nav links)

### Component States
Go through the full state matrix. At minimum:
- Default: [describe]
- Hover: [exact Tailwind — e.g. hover:bg-primary/90]
- Focus-visible: focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
- Active/pressed: active:scale-[0.98] active:bg-primary/80
- Selected: bg-primary text-primary-foreground (nav items, tabs)
- Disabled: opacity-50 pointer-events-none cursor-not-allowed
- Loading: skeleton (animate-pulse, preserves layout) OR spinner (unknown duration)
- Error: border-destructive text-destructive
- Read-only: [if applicable — visible, not editable, not disabled]
- Empty: [new-user variant: show CTA] [zero-results variant: show filter hint]

### TypeScript Interface
interface CardProps {
  title: string
  description?: string
  status: 'active' | 'inactive' | 'pending'
  href: string
}

### Accessibility Requirements
- Role: navigation landmark for nav elements
- aria-current="page" on active nav item
- Focus ring: focus-visible:ring-2 ring-blue-500
- Keyboard: all interactive elements reachable by Tab
- Color contrast: ensure text meets WCAG AA (4.5:1 for body, 3:1 for large)

### What NOT to do
- No fixed px widths — use max-w-* and responsive prefixes
- No inline styles — Tailwind only
- No custom CSS unless CSS variables for theming
```

**Altitude rule:** Specify CSS variables + component names for consistency,
exact Tailwind classes for states and interactions, prose only for atmosphere
("feels slightly elevated, not flat"). Never: exact hex codes. Never: vague
"make it modern."

---

## Phase 2 — Environment Setup

Quick scaffolding. ui-expert owns this, not typescript-expert.

```bash
# New project
npx create-next-app@latest my-app --typescript --tailwind --eslint
cd my-app

# Add shadcn/ui
npx shadcn@latest init

# Add components (reference spec — only add what's needed)
npx shadcn@latest add button card dialog sheet badge skeleton
```

### design.md (optional but powerful)

If the project has a design system, write a `design.md` in the repo root.
It acts as persistent design context for all future component specs:

```markdown
# Design System

## Colors
- Background: bg-zinc-950 (dark) / bg-white (light)
- Surface: bg-zinc-900 / bg-zinc-50
- Border: border-zinc-800 / border-zinc-200
- Accent: bg-blue-600, hover:bg-blue-700

## Typography
- Heading: font-semibold tracking-tight (text-xl to text-3xl)
- Body: text-sm text-zinc-400 / text-zinc-600 (light)
- Code: font-mono text-sm bg-zinc-800 px-1 py-0.5 rounded

## Spacing Scale
- xs: gap-1 / p-1    sm: gap-2 / p-2    md: gap-4 / p-4    lg: gap-6 / p-6

## Motion
- Transitions: transition-colors duration-150 (default)
- No layout-shifting animations on data load — use skeleton instead
```

When `design.md` exists, reference it at the top of every Component Spec.

### Figma MCP (if available)

If a Figma URL is provided, extract design tokens before writing the spec:

```
Use Figma MCP: get_variable_defs on the selection to extract color/spacing/
typography variables. Map them to Tailwind equivalents in the Component Spec.
```

---

## Phase 3 — Implementation Handoff

Once the spec is approved (user has seen the mockup and confirmed direction),
load `typescript-expert` to write the actual components:

```
Skill("typescript-expert")
```

Pass the full **COMPONENT SPEC** block as context. The three-layer context
typescript-expert needs:
1. Design tokens (from Component Spec above)
2. shadcn/ui component list (from Component Spec above)
3. TypeScript interface + states + a11y (from Component Spec above)

**ui-expert does NOT write React/TypeScript implementation code.**
typescript-expert handles: LSP diagnostics, biome linting, bun tooling,
strict typing, imports, and the actual component files.

---

## Phase 4 — Screenshot Verification

After typescript-expert has implemented the components, take a screenshot
to verify the visual output matches the spec:

```bash
af screenshot http://localhost:3000
# Saves screenshot to /tmp/ui-screenshot.png
```

Use Read on the PNG path to view it visually. If the output doesn't match
the spec, either:
- Adjust the Component Spec and re-handoff (design issue)
- Ask typescript-expert to fix specific classes (implementation issue)

---

## shadcn/ui Component Reference

Components live in `components/ui/` — fully owned by you, not a node_module.
Customize them directly.

```tsx
// Always import from local components/ui
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardContent } from "@/components/ui/card"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
```

### Navigation patterns

```
Side nav: Sheet on mobile (SheetTrigger → SheetContent side="left")
          Static aside on desktop (hidden md:flex)
Top nav:  sticky header, backdrop-blur, border-b
```

### Data display

```
Card grid:   grid gap-4 sm:grid-cols-2 lg:grid-cols-3
Table:       shadcn Table (accessible markup, use for tabular data)
```

### Forms

```
Always: react-hook-form + zod + shadcn Form components
Schema: z.object({ field: z.string().email() })
```

### Theme

shadcn uses CSS variables. Edit `globals.css`:

```css
:root {
  --background: 0 0% 100%;
  --primary: 221.2 83.2% 53.3%;
  --radius: 0.5rem;
}
```

Generate full themes at **ui.shadcn.com/themes**.

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Writing React/TypeScript code directly | Produce Component Spec → hand off to typescript-expert |
| Vague design descriptions ("modern", "clean") | Exact token names, Tailwind classes, and states |
| Skipping the spec phase | Always spec before implement — catches misalignment cheaply |
| Hardcoded hex in specs | Use semantic CSS variable names: `bg-primary`, `text-muted-foreground` |
| `leading-relaxed` on headings | Headings need `leading-tight` or `leading-snug` — tight leading at large sizes |
| Flat dark mode (same hex as light) | Lighten brand colors +10–20% luminance; surfaces via luminance steps not shadows |
| Pure white text on dark | Use `text-zinc-100` or `text-zinc-50`, never `text-white` on dark surfaces |
| Generic blue/indigo accent | Require explicit brand color — default to zinc neutrals, not default blue |
| Missing `:focus-visible` | Every interactive element needs a visible keyboard focus ring |
| Disabled = read-only | `disabled` = not interactive, not in tab order; `read-only` = visible and copyable |
| Single empty state | New-user empty (CTA) and zero-results empty (filter hint) are different |
| Importing from `shadcn/ui` npm package | Import from `@/components/ui/` — it's local |
| Fixed px widths | Use `max-w-*`, `container`, responsive prefixes |
| No mobile layout | Always add `sm:` / `md:` breakpoints in spec |
| Skipping screenshot verification | Run `af screenshot` after implementation — trust your eyes |
| Describing designs in text | Use preview server — visual beats verbal every time |

## Outputs

- Component Spec document (design tokens, layout, states, TypeScript interface, a11y)
- Environment scaffolded (Next.js + shadcn/ui configured)
- Optional: `design.md` design system file
- Handoff to typescript-expert for implementation
- Screenshot verification after implementation
