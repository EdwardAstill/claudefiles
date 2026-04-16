---
name: ui-expert
description: >
  Use when building, iterating on, or reviewing UI — React components, Tailwind
  styling, shadcn/ui primitives, responsive layouts, design alternatives, or
  visual verification of what the browser actually renders. Covers three modes:
  (1) website analysis — point at a URL to extract design patterns, tokens,
  layout structure, and component mapping from an existing site;
  (2) design specification — produce a structured component spec using visual
  mockups and the preview server for iteration; (3) implementation handoff —
  scaffold the project environment and produce a spec block that typescript-expert
  consumes to write the actual components. ui-expert owns what things should look
  like; typescript-expert owns the code. Also use for screenshot verification.
---

# UI Expert

Design intelligence for the React + Tailwind + shadcn/ui stack. Can analyze
existing websites to extract design patterns, or specify new designs from
scratch. Hands off to `typescript-expert` for implementation. Visual iteration
via a local preview server. Screenshot verification so Claude can see what the
browser actually renders.

## Stack

**Default:** React + TypeScript + Tailwind CSS + shadcn/ui

This is the most AI-capable frontend stack — widest training data, fewest
hallucinations, best component ecosystem. Use it unless the project already
has a different framework.

---

## Phase 0 — Project Context

**Always do this first** when working in an existing project:

```bash
npx shadcn@latest info --json
```

This gives you the ground truth. Key fields to check before anything else:

| Field | Why it matters |
|-------|---------------|
| `tailwindVersion` | `"v4"` uses `@theme inline` blocks; `"v3"` uses `tailwind.config.js` |
| `tailwindCssFile` | Always edit this file for CSS variables — never create a new one |
| `iconLibrary` | `lucide` → `lucide-react`, `tabler` → `@tabler/icons-react`. Never assume lucide |
| `isRSC` | When `true`, components with hooks/events/browser APIs need `"use client"` |
| `base` | `radix` uses `asChild`; `base` (Base UI) uses `render` prop — affects all component APIs |
| `aliases` | Use the actual import prefix — never hardcode `@/` without checking |
| `components` | What's already installed — don't re-add, don't import what isn't there |
| `packageManager` | Use this for all non-shadcn installs |
| `framework` | Next.js App Router vs Vite SPA vs react-router — affects routing and file conventions |

---

## Website Analysis — "Make it look like X"

When pointed at a URL, analyze the existing site and extract a structured design
breakdown. This feeds directly into a Component Spec — you're reverse-engineering
the design decisions so they can be replicated or adapted in the shadcn/ui stack.

### Workflow

1. **Screenshot the page** — get the visual ground truth

```bash
# firefox-devtools MCP (preferred — uses user's browser with real sessions)
navigate_page(url="https://example.com")
screenshot_page(saveTo="/tmp/site-analysis.png")

# or af browser
af browser start
af browser go https://example.com
af browser snap --full-page --out /tmp/site-analysis.png
```

Read the screenshot to see the actual rendered page.

2. **Capture multiple viewports** — responsive behavior matters

```bash
# Desktop
set_viewport_size(width=1440, height=900)
screenshot_page(saveTo="/tmp/site-desktop.png")

# Tablet
set_viewport_size(width=768, height=1024)
screenshot_page(saveTo="/tmp/site-tablet.png")

# Mobile
set_viewport_size(width=375, height=812)
screenshot_page(saveTo="/tmp/site-mobile.png")
```

3. **Inspect the DOM** — understand structure, not just appearance

```bash
# Get DOM structure with element UIDs
take_snapshot(selector="main", maxLines=100)

# Or with af browser
af browser html "main"
af browser read "main"
```

4. **Extract computed styles** — get actual values, not guesses

```bash
# Via af browser eval — extract the real CSS values
af browser eval "getComputedStyle(document.querySelector('h1')).fontSize"
af browser eval "getComputedStyle(document.querySelector('h1')).fontWeight"
af browser eval "getComputedStyle(document.querySelector('h1')).letterSpacing"
af browser eval "getComputedStyle(document.querySelector('body')).backgroundColor"
af browser eval "getComputedStyle(document.querySelector('body')).fontFamily"
```

For bulk extraction:
```bash
af browser eval "
  const el = document.querySelector('.card');
  const s = getComputedStyle(el);
  JSON.stringify({
    bg: s.backgroundColor,
    border: s.borderColor,
    radius: s.borderRadius,
    padding: s.padding,
    shadow: s.boxShadow
  })
"
```

5. **Screenshot specific components** — isolate individual patterns

```bash
# firefox-devtools
screenshot_by_uid(uid="1_42", saveTo="/tmp/component-nav.png")
screenshot_by_uid(uid="1_85", saveTo="/tmp/component-card.png")

# af browser
af browser snap ".navbar" --out /tmp/component-nav.png
af browser snap ".card" --out /tmp/component-card.png
```

### Output: Design Analysis

Produce a **DESIGN ANALYSIS** block that maps what you found to the shadcn/ui
stack. This becomes the input for a Component Spec.

```
## DESIGN ANALYSIS: <Site Name / URL>

### Source
URL: https://example.com
Screenshots: /tmp/site-desktop.png, /tmp/site-mobile.png

### Color Palette (extracted → mapped to tokens)
- Background: rgb(255,255,255) → bg-background
- Surface/cards: rgb(249,250,251) → bg-card / bg-muted
- Primary action: rgb(59,130,246) → define as --primary: oklch(...)
- Text primary: rgb(17,24,39) → text-foreground
- Text secondary: rgb(107,114,128) → text-muted-foreground
- Border: rgb(229,231,235) → border-border
- Destructive: rgb(239,68,68) → text-destructive

### Typography
- Headings: Inter, 700 weight, -0.02em tracking → font-bold tracking-tight
- Body: Inter, 400 weight, 16px/1.5 → text-base leading-relaxed
- Captions: 12px, 500 weight, +0.05em → text-xs font-medium tracking-wide
- Monospace: JetBrains Mono → font-mono

### Spacing Pattern
- Page padding: 24px → px-6
- Section gap: 64px → gap-16
- Card padding: 24px → p-6
- Card gap: 16px → gap-4
- Inline element gap: 8px → gap-2

### Layout Structure
- Nav: fixed top, full width, h-16, border-b
- Sidebar: 280px fixed left (desktop), Sheet (mobile)
- Content: max-w-7xl mx-auto, responsive grid
- Grid: 3 columns on lg:, 2 on md:, 1 on mobile

### Component Mapping (what they built → shadcn equivalent)
- Top nav bar → custom header with NavigationMenu
- Sidebar nav → Sidebar component
- Data cards → Card + CardHeader + CardContent
- Action buttons → Button (default + outline variants)
- Status pills → Badge (secondary + destructive variants)
- Data table → Table with sortable headers
- Search bar → InputGroup + InputGroupInput + InputGroupAddon
- Modal dialogs → Dialog
- Toast messages → sonner toast()
- Loading states → Skeleton

### Interactions Observed
- Hover: subtle bg change on cards → hover:bg-muted/50
- Transitions: 150ms color transitions → transition-colors duration-150
- Active nav: left border accent → border-l-2 border-primary
- Scroll behavior: sticky header → sticky top-0

### What to replicate vs. adapt
- Replicate: color palette, spacing rhythm, typography scale
- Adapt: [specific components that don't map 1:1 to shadcn/ui]
- Skip: [JS animations, custom widgets better handled differently]
```

### Tips

- **Screenshot first, DOM second.** The visual tells you what matters; the DOM
  tells you how it's built. Don't crawl the entire DOM — focus on what you saw.
- **Extract real values.** `getComputedStyle()` gives you the truth. Don't eyeball
  "looks like 16px" — measure it.
- **Multiple pages matter.** The homepage alone won't show you forms, empty states,
  error pages, or settings layouts. Ask the user which pages to analyze.
- **Login-required sites.** Use `firefox-devtools` MCP — it connects to the user's
  running browser with existing sessions and cookies.
- **Don't over-extract.** The goal is design patterns, not a pixel-perfect clone.
  Map to the nearest shadcn/ui equivalent rather than recreating custom CSS.

---

## Design Intelligence

Core design knowledge applied before writing any component spec. These are the
rules AI most commonly violates.

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
`accent`, `destructive`, `border`, `ring`, `input`, `card`, `popover`, `surface`.

**OKLCH (v4 / modern shadcn):** Colors use `oklch(lightness chroma hue)`. When
editing CSS variables in v4 projects, use OKLCH not HSL. `--primary: oklch(0.205 0 0)`.

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

**What AI gets wrong:** `leading-relaxed` on headings — large text needs tight
leading or it looks broken. Each ramp level needs its own value.

### Spacing — 8pt Grid + Internal ≤ External

All spacing is multiples of 8px. The 4px half-step exists only for icon gaps
and tight inline nudges, not general layout.

**Internal ≤ External rule (Gestalt proximity):** Padding *inside* a group must
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
3. **Brand/accent colors need a lighter variant in dark** — e.g., `blue-600`
   in light → `blue-400` in dark. Increase luminance +10–20%.

**No manual `dark:` overrides** — use semantic tokens (`bg-background`, not
`bg-white dark:bg-zinc-950`). The tokens handle light/dark via CSS variables.

**State overlays (Material Design model):** Hover = 8% overlay, focus = 12%,
active = 12%, dragged = 16%. In Tailwind: `hover:bg-primary/90`.

**No indigo or blue by default** — generic SaaS look. Require explicit brand
color decision. Gray-based neutrals (`zinc`, `slate`) are safe defaults.

**Status indicators** — use `Badge` variants or `text-destructive`. Never raw
`text-emerald-600` / `text-green-500` / `text-red-600` for status colors.

### State Matrix — Every Interactive Component

Spec all of these before handing off to typescript-expert.

| State | Notes | Commonly missed |
|-------|-------|----------------|
| Default | Base appearance | — |
| Hover | `hover:bg-primary/90` or explicit class | — |
| Focus-visible | Keyboard only — `:focus-visible`, never remove rings | Usually forgotten |
| Active/pressed | `active:scale-[0.98] active:bg-primary/80` | Often skipped |
| Disabled | `opacity-50 pointer-events-none cursor-not-allowed` | — |
| Loading | Skeleton (layout preserved) or `<Spinner>` (unknown duration) | Skeleton vs spinner conflated |
| Error/invalid | `border-destructive text-destructive` + `data-invalid` + `aria-invalid` | — |
| Empty (new user) | CTA + onboarding — use `<Empty>` component | Treated same as zero-results |
| Empty (zero results) | "Relax filters" prompt — use `<Empty>` component | Treated same as new-user empty |
| Read-only | Visible + copyable, not editable — NOT the same as disabled | Almost always missing |
| Indeterminate | Checkboxes in trees/tables need it | Almost always missing |
| Selected/active | For nav items, tabs, toggles — `bg-primary text-primary-foreground` | — |

### Semantic HTML First

Never div soup. The spec should name structural elements:
- `<main>`, `<header>`, `<nav>`, `<aside>`, `<section>`, `<article>`, `<footer>`
- `<button>` not `<div onClick>` — keyboard and a11y come free
- `<label>` associated with inputs, always
- `sr-only` for screen-reader text — never `display:none` for accessible content
- Touch targets ≥ 44px on all interactive elements

---

## Critical Rules

These apply everywhere. Violations cause revision cycles.

### Tailwind Patterns

```tsx
// ✗ Wrong — space-y-* and space-x-*
<div className="space-y-4">...</div>

// ✓ Correct — flex + gap-*
<div className="flex flex-col gap-4">...</div>
<div className="flex gap-2">...</div>
```

```tsx
// ✗ Wrong — separate w-* and h-* when equal
<Avatar className="w-10 h-10">

// ✓ Correct — size-* shorthand
<Avatar className="size-10">
```

```tsx
// ✗ Wrong — manual ellipsis
<p className="overflow-hidden text-ellipsis whitespace-nowrap">

// ✓ Correct — truncate shorthand
<p className="truncate">
```

```tsx
// ✗ Wrong — manual dark: overrides
<div className="bg-white dark:bg-zinc-950">

// ✓ Correct — semantic tokens handle it
<div className="bg-background">
```

```tsx
// ✗ Wrong — manual ternary in className
<div className={`flex ${isActive ? "bg-primary text-primary-foreground" : "bg-muted"}`}>

// ✓ Correct — cn() utility
import { cn } from "@/lib/utils"
<div className={cn("flex", isActive ? "bg-primary text-primary-foreground" : "bg-muted")}>
```

```tsx
// ✗ Wrong — manual z-index on overlay components
<DialogContent className="z-50">
<Popover className="z-[999]">

// ✓ Correct — overlays manage their own stacking
<DialogContent>
<Popover>
```

```tsx
// ✗ Wrong — className overrides component styling
<Card className="bg-blue-100 text-blue-900 font-bold">

// ✓ Correct — className for layout only
<Card className="max-w-md mx-auto">
```

### Icon Rules

```tsx
// ✗ Wrong — sizing classes inside components, old mr-2 pattern
<Button>
  <SearchIcon className="mr-2 size-4" />
  Search
</Button>

// ✓ Correct — data-icon attribute, no sizing
<Button>
  <SearchIcon data-icon="inline-start" />
  Search
</Button>
<Button>
  Next
  <ArrowRightIcon data-icon="inline-end" />
</Button>
```

No sizing classes on icons inside components (`Button`, `DropdownMenuItem`,
`Alert`, `Sidebar*`, etc.) — components handle sizing via CSS.

Always use project's `iconLibrary` from info context. Never assume `lucide-react`.

### Forms

```tsx
// ✗ Wrong — raw div layout
<div className="space-y-4">
  <label>Email</label>
  <Input />
</div>

// ✓ Correct — FieldGroup + Field
<FieldGroup>
  <Field>
    <FieldLabel htmlFor="email">Email</FieldLabel>
    <Input id="email" type="email" />
  </Field>
</FieldGroup>

// Validation: data-invalid on Field, aria-invalid on control
<Field data-invalid>
  <FieldLabel htmlFor="email">Email</FieldLabel>
  <Input id="email" aria-invalid />
  <FieldDescription>Invalid email address.</FieldDescription>
</Field>
```

```tsx
// ✗ Wrong — manual Button loop for option sets
{["daily", "weekly", "monthly"].map((v) => (
  <Button key={v} variant={selected === v ? "default" : "outline"} onClick={() => setSelected(v)}>
    {v}
  </Button>
))}

// ✓ Correct — ToggleGroup for 2–7 options
<ToggleGroup spacing={2}>
  <ToggleGroupItem value="daily">Daily</ToggleGroupItem>
  <ToggleGroupItem value="weekly">Weekly</ToggleGroupItem>
  <ToggleGroupItem value="monthly">Monthly</ToggleGroupItem>
</ToggleGroup>
```

```tsx
// ✓ Correct — FieldSet for grouped radios/checkboxes
<FieldSet>
  <FieldLegend variant="label">Preferences</FieldLegend>
  <FieldGroup className="gap-3">
    <Field orientation="horizontal">
      <Checkbox id="dark" />
      <FieldLabel htmlFor="dark" className="font-normal">Dark mode</FieldLabel>
    </Field>
  </FieldGroup>
</FieldSet>
```

```tsx
// ✗ Wrong — Button inside Input with custom positioning
<div className="relative">
  <Input className="pr-10" />
  <Button className="absolute right-0 top-0" size="icon"><SearchIcon /></Button>
</div>

// ✓ Correct — InputGroup + InputGroupAddon
<InputGroup>
  <InputGroupInput placeholder="Search..." />
  <InputGroupAddon>
    <Button size="icon"><SearchIcon data-icon="inline-start" /></Button>
  </InputGroupAddon>
</InputGroup>
```

### Composition

```tsx
// ✗ Wrong — items without their Group wrapper
<SelectContent>
  <SelectItem value="apple">Apple</SelectItem>
</SelectContent>

// ✓ Correct — always inside Group
<SelectContent>
  <SelectGroup>
    <SelectItem value="apple">Apple</SelectItem>
  </SelectGroup>
</SelectContent>
```

Same applies to: `DropdownMenuItem` → `DropdownMenuGroup`, `CommandItem` → `CommandGroup`,
`MenubarItem` → `MenubarGroup`, `ContextMenuItem` → `ContextMenuGroup`.

```tsx
// Dialog, Sheet, Drawer always need a Title
<DialogContent>
  <DialogHeader>
    <DialogTitle>Edit Profile</DialogTitle>   {/* required — sr-only if visually hidden */}
  </DialogHeader>
</DialogContent>
```

```tsx
// Button has no isPending/isLoading prop — compose instead
<Button disabled>
  <Spinner data-icon="inline-start" />
  Saving...
</Button>
```

```tsx
// Avatar always needs AvatarFallback
<Avatar>
  <AvatarImage src="/avatar.png" alt="User" />
  <AvatarFallback>JD</AvatarFallback>
</Avatar>
```

```tsx
// TabsTrigger must be inside TabsList
<Tabs>
  <TabsList>
    <TabsTrigger value="account">Account</TabsTrigger>
  </TabsList>
</Tabs>
```

```tsx
// Card full composition — don't dump into CardContent
<Card>
  <CardHeader>
    <CardTitle>Team</CardTitle>
    <CardDescription>Manage your team.</CardDescription>
  </CardHeader>
  <CardContent>...</CardContent>
  <CardFooter><Button>Invite</Button></CardFooter>
</Card>
```

**Use existing components instead of custom markup:**

| Instead of | Use |
|---|---|
| `<hr>` or `<div className="border-t">` | `<Separator />` |
| `<div className="animate-pulse">` | `<Skeleton className="h-4 w-3/4" />` |
| Custom styled span for labels | `<Badge variant="secondary">` |
| Custom empty state div | `<Empty>` with `EmptyHeader`, `EmptyTitle`, `EmptyContent` |
| `toast()` from other libs | `toast()` from `sonner` |
| Custom callout/info div | `<Alert>` with `AlertTitle` + `AlertDescription` |

---

## Workflow Overview

```
Phase 0 — Context    →  (optional) Analyze  →  Phase 1 — Specify   →  Phase 2 — Environment   →  Phase 3 — Handoff   →  Phase 4 — Verify
npx shadcn info         Point at a URL          Visual exploration      Scaffold or check           Component Spec          Screenshot after
What's installed?       Extract design          Preview server          project setup               for typescript-expert   implementation
isRSC, iconLib,         patterns, tokens        Design tokens           (Next.js + shadcn)          TypeScript interfaces
tailwindVersion         → Design Analysis       Component states        Quick, ui-expert owns       States, tokens, a11y
```

---

## Phase 1 — Design Specification

Before code, produce a **Component Spec**. Design intelligence phase — what should
it look like, how should it behave, what states exist?

### Search before building

```bash
# Check if a shadcn component or block already exists
npx shadcn@latest search @shadcn -q "sidebar"
npx shadcn@latest search @tailark -q "stats card"
npx shadcn@latest search @magicui -q "shimmer"
```

If something exists, use it. Don't write custom markup for things shadcn ships.

### Get docs before using

```bash
# Always run before working with a component
npx shadcn@latest docs button dialog select
```

This returns the docs URL — fetch it to get correct API, props, and examples.

### 1a — Visual Exploration

When the user needs to choose between design options, use the preview server to
show rendered options — visual beats verbal every time.

```bash
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

### 1b — Component Spec

Output a **COMPONENT SPEC** block. This is the contract between ui-expert
and typescript-expert. Be precise — exact token names, not prose.

```
## COMPONENT SPEC: <ComponentName>

### Project Context
(From npx shadcn@latest info — Tailwind v3/v4, isRSC, base, iconLibrary)
"use client" required: [yes/no] — [reason if yes]

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
- Card + CardHeader + CardTitle + CardContent + CardFooter — data panels
- Button variant="outline" — secondary actions
- Badge variant="secondary" — status labels
- ToggleGroup — view switcher (2–3 options)
- (Do NOT use: DropdownMenu for this — use plain nav links)

### Component States
(See full state matrix. At minimum:)
- Default: [describe]
- Hover: [exact Tailwind — e.g. hover:bg-primary/90]
- Focus-visible: focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
- Active/pressed: active:scale-[0.98] active:bg-primary/80
- Selected: bg-primary text-primary-foreground (nav items, tabs)
- Disabled: opacity-50 pointer-events-none cursor-not-allowed
- Loading: <Spinner data-icon="inline-start" /> + disabled (button); <Skeleton /> (content)
- Error: data-invalid on Field, aria-invalid on control, border-destructive text-destructive
- Read-only: [if applicable — visible, not editable, not disabled]
- Empty (new-user): <Empty> with CTA
- Empty (zero-results): <Empty> with filter hint

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
- DialogTitle/SheetTitle required (sr-only if visually hidden)
- Focus ring: focus-visible:ring-2 ring-ring ring-offset-background
- Keyboard: all interactive elements reachable by Tab
- Color contrast: WCAG AA (4.5:1 body, 3:1 large text)

### What NOT to do
- No space-x-* / space-y-* — use flex gap-*
- No fixed px widths — use max-w-* and responsive prefixes
- No inline styles — Tailwind only
- No custom CSS unless CSS variables for theming
- No manual dark: overrides — use semantic tokens
- No sizing classes on icons inside components
```

**Altitude rule:** CSS variables + component names for consistency, exact Tailwind
classes for states and interactions, prose only for atmosphere. Never: hex codes.
Never: vague "make it modern."

---

## Phase 2 — Environment Setup

```bash
# New project — use a named preset
npx shadcn@latest init --name my-app --preset base-nova
npx shadcn@latest init --name my-app --preset base-nova --template vite
npx shadcn@latest init --name my-app --preset base-nova --monorepo

# Named presets: nova, vega, maia, lyra, mira, luma
# Templates: next (default), vite, start, react-router, astro, laravel

# Existing project — add components (check info first, only add what's missing)
npx shadcn@latest search @shadcn -q "<what you need>"
npx shadcn@latest add button card dialog sheet badge skeleton
npx shadcn@latest add @magicui/shimmer-button    # community registry

# Preview before adding/updating
npx shadcn@latest add button --dry-run
npx shadcn@latest add button --diff button.tsx   # see what changed
```

### design.md (optional but powerful)

If the project has a design system, write a `design.md` in the repo root:

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

### Tailwind v4 (when `tailwindVersion === "v4"`)

v4 uses `@theme inline` in CSS instead of `tailwind.config.js`:

```css
@import "tailwindcss";
@import "tw-animate-css";

@custom-variant dark (&:is(.dark *));

@theme inline {
  --radius-sm: calc(var(--radius) - 4px);
  --color-background: var(--background);
  --color-primary: var(--primary);
  /* etc. */
}

:root {
  --radius: 0.625rem;
  --background: oklch(1 0 0);
  --primary: oklch(0.205 0 0);
}
```

### Figma MCP (if available)

If a Figma URL is provided:
```
Use Figma MCP: get_variable_defs on the selection to extract color/spacing/
typography variables. Map them to Tailwind equivalents in the Component Spec.
```

---

## Phase 3 — Implementation Handoff

Once the spec is approved, load `typescript-expert`:

```
Skill("typescript-expert")
```

Pass the full **COMPONENT SPEC** block as context. Three-layer context needed:
1. Design tokens (from Component Spec)
2. shadcn/ui component list (from Component Spec)
3. TypeScript interface + states + a11y (from Component Spec)

**ui-expert does NOT write React/TypeScript implementation code.**
typescript-expert handles: LSP diagnostics, biome linting, bun tooling,
strict typing, imports, and the actual component files.

After typescript-expert adds components, verify imports match the installed
components from `npx shadcn@latest info` — don't import what isn't there.

---

## Phase 4 — Screenshot Verification

```bash
af screenshot http://localhost:3000
```

Use Read on the PNG path to view it visually. If output doesn't match:
- Adjust Component Spec and re-handoff (design issue)
- Ask typescript-expert to fix specific classes (implementation issue)

---

## Component Selection

| Need | Use |
|------|-----|
| Button / action | `Button` with variant (default, outline, ghost, destructive) |
| 2–7 toggle options | `ToggleGroup` + `ToggleGroupItem` — not manual Button loop |
| Form inputs | `Input`, `Select`, `Combobox`, `Switch`, `Checkbox`, `RadioGroup`, `Textarea`, `Slider` |
| Input with button | `InputGroup` + `InputGroupInput` + `InputGroupAddon` |
| Option groups | `FieldGroup` + `Field` + `FieldLabel` — not raw div/label |
| Grouped radios/checkboxes | `FieldSet` + `FieldLegend` + `FieldGroup` |
| Data display | `Table`, `Card` (full composition), `Badge`, `Avatar` + `AvatarFallback` |
| Navigation | `Sidebar`, `NavigationMenu`, `Breadcrumb`, `Tabs` (in `TabsList`), `Pagination` |
| Modal / focused task | `Dialog` (requires `DialogTitle`) |
| Destructive confirm | `AlertDialog` |
| Side panel | `Sheet` (requires `SheetTitle`) |
| Bottom sheet | `Drawer` (requires `DrawerTitle`) |
| Quick hover info | `HoverCard` |
| Small click popover | `Popover` |
| Toast notifications | `sonner` — `toast()`, `toast.success()`, `toast.error()` |
| Loading (layout preserved) | `Skeleton` — not custom `animate-pulse` div |
| Loading (button/action) | `<Spinner data-icon="inline-start" />` + `disabled` — no `isPending` prop |
| Empty state (new user) | `Empty` + `EmptyHeader` + `EmptyMedia` + `EmptyContent` |
| Empty state (no results) | `Empty` with filter hint |
| Callout / info | `Alert` + `AlertTitle` + `AlertDescription` |
| Charts | `Chart` (wraps Recharts) |
| Command palette | `Command` inside `Dialog` |
| Menus | `DropdownMenu`, `ContextMenu`, `Menubar` (items always in Group) |
| Dividers | `Separator` — not `<hr>` or `<div className="border-t">` |
| Status labels | `Badge` variant — not custom styled spans |
| Layout | `Card`, `Resizable`, `ScrollArea`, `Accordion`, `Collapsible` |

---

## shadcn/ui Quick Reference

```tsx
// Always import from local components/ui — never from npm package
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card"

// Navigation
// Sheet on mobile, static aside on desktop
<Sheet><SheetTrigger><SheetContent side="left"><SheetTitle>...</SheetTitle>

// Data grids
grid gap-4 sm:grid-cols-2 lg:grid-cols-3

// Theme — edit the file from npx shadcn@latest info tailwindCssFile
:root { --primary: oklch(0.205 0 0); --radius: 0.5rem; }

// Generate themes at ui.shadcn.com/themes
// Apply: npx shadcn@latest apply --preset a2r6bw
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Writing React/TypeScript code directly | Produce Component Spec → hand off to typescript-expert |
| Skipping `npx shadcn@latest info` | Always run first — know isRSC, iconLibrary, tailwindVersion |
| Building what shadcn ships | `npx shadcn@latest search` first — use existing components |
| Using component without docs | `npx shadcn@latest docs <name>` before any component work |
| `space-y-*` / `space-x-*` | Use `flex flex-col gap-*` / `flex gap-*` |
| `w-10 h-10` when equal | Use `size-10` |
| Manual ellipsis classes | Use `truncate` |
| `dark:bg-zinc-950` manual override | Use `bg-background` — semantic tokens handle dark |
| Manual ternary in className | Use `cn()` utility |
| `z-50` on Dialog/Sheet/Popover | Remove — overlays manage stacking |
| `className="bg-blue-100"` on Card | `className` is layout only — use variants or tokens |
| `<SearchIcon className="mr-2 size-4" />` in Button | `<SearchIcon data-icon="inline-start" />` |
| Assuming `lucide-react` for icons | Check `iconLibrary` from project info |
| Raw `<div>` form layout | `FieldGroup` + `Field` + `FieldLabel` |
| Button loop for option sets | `ToggleGroup` for 2–7 options |
| `border-destructive` only for error | Add `data-invalid` on `Field` + `aria-invalid` on control |
| `<Input>` inside `<InputGroup>` | `<InputGroupInput>` inside `<InputGroup>` |
| Missing `DialogTitle`/`SheetTitle` | Always required — `sr-only` if visually hidden |
| `Button disabled isLoading` | Doesn't exist — compose `<Spinner data-icon="inline-start" />` + `disabled` |
| `<TabsTrigger>` outside `<TabsList>` | Always wrap triggers in `<TabsList>` |
| No `<AvatarFallback>` | Always include — renders when image fails |
| `<SelectItem>` without `<SelectGroup>` | Always wrap items in their Group component |
| Custom empty state div | Use `<Empty>` component |
| `<hr>` or `<div className="border-t">` | Use `<Separator>` |
| Custom `animate-pulse` loading | Use `<Skeleton>` |
| Custom styled `<span>` for labels | Use `<Badge>` |
| Hardcoded hex in specs | Use semantic CSS variable names: `bg-primary`, `text-muted-foreground` |
| `leading-relaxed` on headings | Headings need `leading-tight` or `leading-snug` |
| Flat dark mode (same hex as light) | Lighten brand colors +10–20% luminance |
| Pure white text on dark | `text-zinc-100` or `text-zinc-50`, never `text-white` on dark |
| Generic blue/indigo accent | Require explicit brand color — default to zinc neutrals |
| Missing `:focus-visible` | Every interactive element needs a visible keyboard focus ring |
| Disabled = read-only | `disabled` = not interactive; `read-only` = visible and copyable |
| Single empty state | New-user empty (CTA) and zero-results empty (filter hint) are different |
| Importing from `shadcn/ui` npm | Import from `@/components/ui/` — it's local |
| Fixed px widths | Use `max-w-*`, `container`, responsive prefixes |
| No mobile layout | Always add `sm:` / `md:` breakpoints in spec |
| Skipping screenshot verification | Run `af screenshot` after implementation — trust your eyes |
| Describing designs in text | Use preview server — visual beats verbal |
| Guessing colors from a reference site | Use `getComputedStyle()` to extract actual values |
| Analyzing only the homepage | Ask which pages to analyze — forms, settings, empty states differ |
| Pixel-perfect cloning from URL | Map to nearest shadcn/ui equivalent — patterns, not pixels |

## Outputs

- Component Spec (design tokens, layout, states, TypeScript interface, a11y)
- Environment scaffolded (Next.js + shadcn/ui configured, correct preset)
- Optional: `design.md` design system file
- Handoff to typescript-expert for implementation
- Screenshot verification after implementation
