---
name: typst-expert
description: >
  Typst document expert. Use when writing or debugging Typst documents —
  markup, custom functions, styling, packages, and compilation. Uses the
  tinymist LSP for live introspection and typst.app/docs for reference.
---

# Typst Expert

Typst is a modern typesetting system — think LaTeX with a sane syntax.
Handles document structure, custom functions, styling, and the typst package
ecosystem. Uses tinymist for LSP support.

## LSP — tinymist

tinymist is the official Typst language server. Provides completions, hover
docs, diagnostics, and symbol navigation for `.typ` files.

```
LSP: hover       — function signatures, parameter docs
LSP: diagnostics — syntax errors, undefined variables, type mismatches
LSP: definition  — jump to function or variable definition
LSP: completions — context-aware completions for functions and packages
```

Install: `cargo install tinymist`

## Documentation

- **Language reference:** fetch from `https://typst.app/docs/reference/` — most reliable source
- **Packages:** fetch from `https://typst.app/universe/` — browse available packages
- **context7:** coverage is thin — prefer WebFetch on typst.app/docs directly
- **Function signatures:** use LSP hover first; fall back to docs.typst.app

Always check the installed Typst version — the language evolves quickly.
```bash
typst --version
```

## Toolchain

| Tool | Purpose | Command |
|------|---------|---------|
| `typst compile` | Compile to PDF | `typst compile doc.typ` |
| `typst watch` | Recompile on save | `typst watch doc.typ` |
| `tinymist` | LSP server | via editor |
| `typst query` | Extract metadata | `typst query doc.typ <selector>` |

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

## Outputs

- Compiling `.typ` file to PDF
- LSP diagnostics for any file reviewed
- Typst package recommendations with version pins
