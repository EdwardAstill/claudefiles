---
name: ui-expert
description: >
  Use when building, iterating on, or reviewing UI — React components, Tailwind
  styling, shadcn/ui primitives, responsive layouts, design alternatives, or
  visual verification of what the browser actually renders. Use when the task
  involves any frontend visual work regardless of complexity.
---

# UI Expert

React + Tailwind + shadcn/ui stack. Visual iteration via a local preview server.
Screenshot verification so Claude can see what the browser actually renders.

## Stack

**Default:** React + TypeScript + Tailwind CSS + shadcn/ui

This is the most AI-capable frontend stack — widest training data, fewest
hallucinations, best component ecosystem. Use it unless the project already
has a different framework.

## Quick Setup

```bash
# New project
npx create-next-app@latest my-app --typescript --tailwind --eslint
cd my-app

# Add shadcn/ui
npx shadcn@latest init

# Add components
npx shadcn@latest add button card dialog sheet sidebar nav-menu
```

## shadcn/ui — Key Patterns

Components live in `components/ui/` and are fully owned by you (not a node_module).
Customise them directly.

```tsx
// Import from local components/ui, not from npm
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardContent } from "@/components/ui/card"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"

// Compose — shadcn is primitives, not complete widgets
export function Sidebar() {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="icon"><Menu /></Button>
      </SheetTrigger>
      <SheetContent side="left">
        <nav>...</nav>
      </SheetContent>
    </Sheet>
  )
}
```

## Tailwind — Idiomatic Patterns

```tsx
// Responsive layout
<div className="flex flex-col md:flex-row gap-4">

// Dark mode
<div className="bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100">

// cn() for conditional classes (from shadcn/ui lib/utils)
import { cn } from "@/lib/utils"
<div className={cn("base-classes", isActive && "active-classes", className)}>

// Typography scale
<h1 className="text-3xl font-bold tracking-tight">
<p className="text-sm text-muted-foreground">
```

## Visual Iteration Workflow

When the user needs to choose between design options (side menu vs top nav,
this theme vs that theme, card layout vs table), use the preview server to
show real rendered options rather than describing them in text.

### Step 1 — Generate HTML mockups

Write one HTML file per design option into `/tmp/ui-preview/`:

```python
# Each file is a complete HTML document or fragment
# Name them option-a.html, option-b.html etc.
# The preview server serves the newest file automatically
```

Keep mockups self-contained: inline Tailwind via CDN, no build step needed.

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.tailwindcss.com"></script>
  <title>Option A — Side Menu</title>
</head>
<body class="flex h-screen bg-zinc-50">
  <!-- Option A layout here -->
</body>
</html>
```

### Step 2 — Start preview server

```bash
cf preview /tmp/ui-preview/
# Opens browser automatically at http://localhost:PORT
# Write new HTML files to show them; server auto-refreshes
```

### Step 3 — Read user choice

The server records clicks to `/tmp/ui-preview/events.jsonl`.
Each line: `{"type": "click", "choice": "option-a", "timestamp": "..."}`.
Read this file to see what the user picked.

### Step 4 — Take screenshot to verify

After implementing a design in the actual app, take a screenshot to verify:

```bash
cf screenshot http://localhost:3000
# Saves screenshot to /tmp/ui-screenshot.png
# Claude reads this image to verify layout, spacing, colours
```

Use Read on the PNG path to view it visually.

## Component Patterns

### Navigation — Side vs Top

```tsx
// Side nav (Sheet on mobile, static on desktop)
<aside className="hidden md:flex w-64 flex-col border-r bg-background">
  <nav className="flex-1 px-4 py-6 space-y-1">
    {items.map(item => (
      <Link key={item.href} href={item.href}
        className={cn("flex items-center gap-3 rounded-lg px-3 py-2 text-sm",
          pathname === item.href
            ? "bg-primary text-primary-foreground"
            : "text-muted-foreground hover:bg-accent"
        )}>
        <item.icon className="h-4 w-4" />
        {item.label}
      </Link>
    ))}
  </nav>
</aside>

// Top nav
<header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur">
  <div className="container flex h-14 items-center justify-between">
    <Logo />
    <nav className="flex items-center gap-6 text-sm">
      {items.map(item => <NavLink key={item.href} {...item} />)}
    </nav>
  </div>
</header>
```

### Data Display

```tsx
// Card grid
<div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
  {items.map(item => (
    <Card key={item.id}>
      <CardHeader><CardTitle>{item.title}</CardTitle></CardHeader>
      <CardContent>{item.body}</CardContent>
    </Card>
  ))}
</div>

// Table (use shadcn Table for accessible markup)
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
```

### Forms

```tsx
// Always use react-hook-form + zod for validation
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form"

const schema = z.object({ email: z.string().email(), name: z.string().min(2) })

export function MyForm() {
  const form = useForm({ resolver: zodResolver(schema) })
  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField control={form.control} name="email" render={({ field }) => (
          <FormItem>
            <FormLabel>Email</FormLabel>
            <FormControl><Input {...field} /></FormControl>
            <FormMessage />
          </FormItem>
        )} />
        <Button type="submit">Submit</Button>
      </form>
    </Form>
  )
}
```

## Theme Customisation

shadcn uses CSS variables. Edit `globals.css` to change the theme:

```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 221.2 83.2% 53.3%;   /* change this for brand colour */
  --primary-foreground: 210 40% 98%;
  --radius: 0.5rem;                /* change for border radius feel */
}
```

Generate full themes at: **ui.shadcn.com/themes**

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Importing from `shadcn/ui` npm package | Import from `@/components/ui/` — it's local |
| Custom CSS instead of Tailwind | Use Tailwind utilities; cn() for conditionals |
| Layout with fixed px widths | Use `max-w-*`, `container`, responsive prefixes |
| No mobile layout | Always add `sm:` / `md:` breakpoints |
| Skipping screenshot verification | Run `cf screenshot` after implementing — trust your eyes |
| Describing designs in text | Use preview server — visual beats verbal every time |

## Outputs

- React + TypeScript components using shadcn/ui primitives
- Tailwind-styled, responsive, dark-mode-ready
- Visually verified via screenshot before declaring done
- Design alternatives shown in browser via preview server when choices exist
