---
name: typst-expert
description: >
  Use when writing, styling, or debugging Typst documents. Trigger
  phrases: "write this document in Typst", "Typst template for a
  report", "custom Typst function for X", "Typst won't compile", "how
  do I do footnotes in Typst", "import a Typst package", "style a
  heading in Typst", "convert this LaTeX to Typst", "Typst math
  formula for X", "tinymist LSP error". Uses tinymist for live
  diagnostics and fetches reference from typst.app/docs. Do NOT use
  for LaTeX (the model handles that directly), general markdown /
  README writing (use documentation), or PDF post-processing (use
  file-converter).
includes:
  - typst/tinymist
---

# Typst Expert

Typst is a modern typesetting system — think LaTeX with a sane syntax.
Handles document structure, custom functions, styling, and the typst package
ecosystem. LSP workflow, tinymist install, config, and diagnostics live in the
`typst/tinymist` fragment (see `## Shared Conventions`); this file is for
Typst-specific markup patterns and the document toolchain.

## Documentation

- **Language reference:** fetch from `https://typst.app/docs/reference/` — most reliable source
- **Packages:** fetch from `https://typst.app/universe/` — browse available packages
- **context7:** coverage is thin — prefer WebFetch on typst.app/docs directly
- **Function signatures:** use LSP hover first; fall back to docs.typst.app

Always check the installed Typst version — the language evolves quickly.
```bash
typst --version
```

## Toolchain at a glance

| Tool            | Purpose               | Covered in fragment   |
|-----------------|-----------------------|-----------------------|
| `typst compile` | Compile to PDF        | inline below          |
| `typst watch`   | Recompile on save     | `typst watch doc.typ` |
| `tinymist`      | LSP server            | `typst/tinymist`      |
| `typst query`   | Extract metadata      | `typst query doc.typ <selector>` |
| `typstyle`      | Formatter             | see `typst/tinymist`  |

## Document Structure

```typst
#set document(title: "My Document", author: "Name")
#set page(paper: "a4", margin: 2cm)
#set text(font: "New Computer Modern", size: 11pt)

= Heading

Some *bold* and _italic_ text. A @reference.

#figure(
  image("fig.png", width: 80%),
  caption: [A figure caption],
) <fig-label>
```

## Custom Functions

```typst
// Define reusable components
#let note(body) = block(
  fill: luma(240),
  inset: 8pt,
  radius: 4pt,
  body
)

// Use it
#note[This is a callout note.]
```

## Packages

Import from the Typst package universe:
```typst
#import "@preview/cetz:0.2.2": canvas, draw
```

Browse available packages at typst.app/universe. Pin exact versions in documents.

## Math

Typst has first-class math support:
```typst
The equation $E = m c^2$ is inline.

$ sum_(i=1)^n i = (n(n+1))/2 $ // display math
```

## Idiomatic Patterns

**Use `#set` rules** for global styling rather than inline formatting everywhere.

**Use `#show` rules** to transform specific elements:
```typst
#show heading: it => text(blue, it)
```

**Name figures and equations** with `<label>` syntax for cross-referencing with `@label`.

**Separate content from style** — put `#set` and `#show` rules at the top, content below.

## Anti-patterns

| Anti-pattern | Instead |
|-------------|---------|
| Hardcoding spacing everywhere | Use `#set` rules for consistent spacing |
| Copy-pasting repeated blocks | Define a `#let` function |
| Using `#v()` to push content around | Use layout primitives (`grid`, `columns`) |
| Importing without version pins | Always pin: `@preview/pkg:0.1.2` |

## Document Types

**Article / report:**
```typst
#set document(title: "Report", author: "Name")
#set page(paper: "a4", margin: (top: 2cm, rest: 2.5cm))
#set heading(numbering: "1.1")
```

**Slides** (using polylux):
```typst
#import "@preview/polylux:0.3.1": *
#set page(paper: "presentation-16-9")

#polylux-slide[
  = Title slide
  Subtitle text
]
```

**CV:**
```typst
#import "@preview/brilliant-cv:2.0.0": cvSection, cvEntry
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Forgetting `#` before function calls | `#text(red)[...]` not `text(red)[...]` |
| Confusing string `"hello"` and content `[hello]` | Functions taking content use `[...]`, not `"..."` |
| Math outside `$...$` delimiters | Always wrap math: `$x^2 + y^2$` |
| Inline styles instead of `#show` rules | Use `#show heading: ...` for consistent styling |
| Missing version pins on packages | Always `@preview/pkg:0.1.2`, not `@preview/pkg` |
| Using `#v()` for layout | Use `grid`, `columns`, or `stack` instead |

## Outputs

- Compiling `.typ` file to PDF
- LSP diagnostics for any file reviewed
- Typst package recommendations with version pins
