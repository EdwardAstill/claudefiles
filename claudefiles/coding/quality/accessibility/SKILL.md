---
name: accessibility
description: >
  Use when building or reviewing web UI for accessibility compliance. Covers
  WCAG 2.1 AA, semantic HTML, ARIA attributes, keyboard navigation, screen
  reader testing, and color contrast requirements. Tools: axe-core, Lighthouse.
  Low-priority — invoke when a11y is the stated requirement or during UI review.
---

# Accessibility

Web and UI accessibility compliance — making applications usable by everyone,
including people who use assistive technologies.

**Core principle:** Accessibility is not an afterthought or a checklist.
It's a design constraint that produces better software for all users.

## When to Use

- Building new UI components (forms, modals, navigation, tables)
- Reviewing existing UI for WCAG 2.1 AA compliance
- Fixing accessibility audit findings
- Adding keyboard navigation to interactive components
- Implementing ARIA attributes for custom widgets
- Checking color contrast and visual accessibility
- Setting up automated a11y testing in CI

## When NOT to Use

- **Backend/API work** — no UI to make accessible
- **CLI tools** — different accessibility considerations (not covered here)
- **Visual design** — this skill is for implementation, not design decisions
- **Performance of UI rendering** — use `performance-profiling`

## The Iron Law

```
SEMANTIC HTML FIRST, ARIA SECOND, CUSTOM WIDGETS LAST
```

Native HTML elements have built-in accessibility. Use them. Only reach for
ARIA when HTML doesn't have what you need. Custom widgets must replicate
all native behavior (keyboard, focus, screen reader announcements).

## WCAG 2.1 AA Quick Reference

The four principles — content must be:

| Principle | Meaning | Key Requirements |
|-----------|---------|-----------------|
| **Perceivable** | Users can perceive the content | Text alternatives, captions, contrast |
| **Operable** | Users can interact with the UI | Keyboard accessible, no time traps, no seizure triggers |
| **Understandable** | Users can understand the content | Readable, predictable, input assistance |
| **Robust** | Content works with assistive tech | Valid HTML, ARIA used correctly |

## Process

### Phase 1: Semantic Structure

1. **Use correct heading hierarchy** — `h1` → `h2` → `h3`, never skip levels
2. **Use landmark elements** — `<header>`, `<nav>`, `<main>`, `<footer>`, `<aside>`
3. **Use semantic elements** — `<button>` not `<div onclick>`, `<a>` for navigation
4. **Forms need labels** — every `<input>` must have an associated `<label>`
5. **Tables need headers** — `<th>` with `scope` attribute, `<caption>` for context
6. **Lists for list content** — `<ul>`/`<ol>` not styled `<div>`s

```html
<!-- BAD: div soup -->
<div class="button" onclick="submit()">Submit</div>

<!-- GOOD: semantic HTML -->
<button type="submit">Submit</button>

<!-- BAD: missing label -->
<input type="email" placeholder="Email">

<!-- GOOD: explicit label -->
<label for="email">Email address</label>
<input id="email" type="email" autocomplete="email">
```

### Phase 2: Keyboard Navigation

Every interactive element must be:
1. **Focusable** — can reach it with Tab / Shift+Tab
2. **Operable** — can activate with Enter or Space
3. **Visible focus** — focus indicator is clearly visible (never `outline: none`)

**Common keyboard patterns:**

| Component | Keys |
|-----------|------|
| Links, buttons | Tab to focus, Enter to activate |
| Checkboxes | Tab to focus, Space to toggle |
| Radio groups | Tab to group, Arrow keys between options |
| Dropdowns/menus | Tab to open, Arrow keys to navigate, Enter to select, Escape to close |
| Modals | Focus trapped inside, Escape to close, focus returns to trigger on close |
| Tabs | Tab to tab list, Arrow keys between tabs, Tab into panel |

**Focus management for SPAs:**
- When content changes dynamically, move focus to the new content
- Route changes should move focus to the main heading or content area
- Announce dynamic changes with `aria-live` regions

### Phase 3: ARIA (When HTML Isn't Enough)

**Five rules of ARIA:**
1. Don't use ARIA if native HTML works
2. Don't change native semantics (`<h2 role="button">` is wrong)
3. All interactive ARIA elements must be keyboard accessible
4. Don't use `role="presentation"` or `aria-hidden="true"` on focusable elements
5. All interactive elements must have accessible names

```html
<!-- Custom toggle: needs ARIA because there's no native HTML toggle -->
<button
  role="switch"
  aria-checked="false"
  aria-label="Dark mode"
  onclick="toggleDarkMode(this)"
>
  <span class="toggle-thumb"></span>
</button>

<!-- Live region for dynamic updates -->
<div aria-live="polite" aria-atomic="true">
  3 items in your cart
</div>

<!-- Accessible modal -->
<div role="dialog" aria-modal="true" aria-labelledby="dialog-title">
  <h2 id="dialog-title">Confirm deletion</h2>
  <!-- modal content -->
</div>
```

### Phase 4: Visual Accessibility

**Color contrast requirements (WCAG AA):**

| Element | Minimum Ratio |
|---------|--------------|
| Normal text (< 18px) | 4.5:1 |
| Large text (>= 18px bold, >= 24px) | 3:1 |
| UI components and graphical objects | 3:1 |

**Never convey information by color alone.** Add icons, patterns, or text labels.

```css
/* BAD: only color indicates error */
.error { color: red; }

/* GOOD: color + icon + text */
.error {
  color: #d32f2f;
  border-left: 3px solid #d32f2f;
}
.error::before {
  content: "⚠ Error: ";
}
```

**Respect user preferences:**
```css
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}

@media (prefers-color-scheme: dark) {
  /* dark mode styles maintaining contrast ratios */
}
```

## Automated Testing

```bash
# Lighthouse accessibility audit
npx lighthouse http://localhost:3000 --only-categories=accessibility --output=json

# axe-core in tests (jest + testing-library)
# npm install --save-dev jest-axe
```

```javascript
// jest-axe integration
import { axe, toHaveNoViolations } from "jest-axe";
expect.extend(toHaveNoViolations);

test("form has no a11y violations", async () => {
  const { container } = render(<LoginForm />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

```javascript
// Playwright accessibility testing
test("page passes axe checks", async ({ page }) => {
  await page.goto("/");
  const violations = await new AxeBuilder({ page }).analyze();
  expect(violations.violations).toEqual([]);
});
```

## Anti-patterns

| Anti-pattern | Why It's Bad | Instead |
|-------------|-------------|---------|
| `<div onclick>` instead of `<button>` | No keyboard support, no role, no focus | Use `<button>` |
| `outline: none` without replacement | Keyboard users can't see focus | Custom visible focus style |
| Images without `alt` text | Screen readers say "image" with no context | Descriptive `alt`, or `alt=""` for decorative |
| `aria-label` on non-interactive elements | Screen readers may ignore it | Use visible text or `aria-labelledby` |
| Autoplaying video/audio | Disorienting, blocks screen readers | Require user action to play |
| Color-only error indication | Invisible to colorblind users | Color + icon + text |
| Tab index > 0 | Creates unpredictable focus order | Use `tabindex="0"` or `-1` only |
| Missing skip-to-content link | Keyboard users must tab through entire nav | Add as first focusable element |

## Tools

| Tool | Purpose | Usage |
|------|---------|-------|
| axe-core | Automated a11y testing library | Integrates with jest, Playwright, Cypress |
| Lighthouse | Comprehensive audit (including a11y) | Chrome DevTools or CLI |
| WAVE | Browser extension for visual a11y review | Install in browser |
| NVDA | Free screen reader (Windows) | Manual testing |
| VoiceOver | Built-in screen reader (macOS/iOS) | Cmd+F5 to activate |
| Contrast Checker | Color contrast ratio calculator | webaim.org/resources/contrastchecker |
| eslint-plugin-jsx-a11y | Lint JSX for a11y issues | Add to ESLint config |
| pa11y | CLI accessibility testing | `npx pa11y http://localhost:3000` |

## Outputs

- Audit report listing WCAG violations with severity and remediation
- Fixed components with semantic HTML, ARIA, and keyboard support
- Automated a11y tests (axe-core) integrated into test suite
- Color contrast verification for all text and UI elements
- Chain into `verification-before-completion` to confirm fixes pass axe audit
