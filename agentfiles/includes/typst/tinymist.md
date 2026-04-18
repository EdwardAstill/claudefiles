---
name: typst/tinymist
---

# tinymist — LSP Workflow

tinymist is the official Typst language server and the primary tool for
authoring `.typ` files in this suite. Always run diagnostics before
suggesting fixes — a Typst parse error one line earlier will cascade into
misleading compile output, and hover docs beat guessing at a function
signature from memory.

## LSP verbs (prefer over CLI)

```
LSP: hover       — function signature + parameter docs for any symbol
LSP: diagnostics — syntax errors, undefined identifiers, type mismatches
LSP: definition  — jump to a `#let` or package symbol definition
LSP: completions — context-aware function / parameter / package suggestions
LSP: references  — find all uses of a `#let` or `<label>`
```

Reach for the LSP before shelling out to `typst compile` to see an error.
The LSP reports diagnostics per-keystroke; the CLI only fires on a full
rebuild and swallows structured location info in some cases.

## Install / invoke

```bash
cargo install tinymist                # official Rust build
# or:
brew install tinymist                 # on macOS
```

Launch modes:

- **Editor-integrated** — the common case. Neovim (`nvim-lspconfig`),
  VSCode (`myriad-dreamin.tinymist`), Helix, Zed all ship support.
- **Standalone** — `tinymist lsp` over stdio, for custom clients or
  scripting diagnostics in CI.

## Common config

tinymist reads project settings from `tinymist.toml` at the repo root (or
workspace settings in the editor). Reasonable defaults:

```toml
# tinymist.toml
root_dir = "."
output_path = "build"
export_pdf = "onSave"          # or "onType" for live preview
preview.background = "#1e1e1e"
formatter_mode = "typstyle"    # `typstfmt` is the older option
```

- `export_pdf = "onSave"` gives you a fresh PDF every save without
  spamming the filesystem on every keystroke.
- Pin `typst_extra_args = ["--root", "."]` if the document imports from
  sibling files — Typst's default root is the document directory.

## Interpreting diagnostics

- **`unknown variable`** — you referenced a `#let` that isn't in scope.
  Either it's below the first use (Typst is top-down), or you forgot a
  `#import`.
- **`expected content, found string`** — a function wants `[...]`, you
  passed `"..."`. Typst distinguishes string literals from content blocks.
- **`file not found`** — package path typo or missing version pin. Always
  `@preview/pkg:0.1.2`, never bare `@preview/pkg`.
- **`type mismatch: expected length, found integer`** — Typst is strict
  about units. Write `2pt` / `1em` / `80%`, not `2`.

If the LSP disagrees with what the CLI produces, trust the LSP — it was
run against the exact source in the editor buffer, not a stale file on
disk.

## tinymist + typst compile + typstyle

- Run `typstyle` (or the legacy `typstfmt`) before compile to keep diffs
  quiet. tinymist can do this on save via `formatter_mode`.
- `typst watch doc.typ` in a terminal complements the LSP: the LSP
  catches errors as you type, `watch` confirms the PDF actually renders.
- In CI: `typst compile --font-path fonts/ doc.typ` with an explicit font
  path so builds are reproducible across machines.

## Outputs expected from skills using tinymist

- An LSP diagnostics report for any `.typ` file reviewed.
- `typst compile` clean — no warnings, no missing fonts, no unresolved
  package imports.
- Any `#let` or custom function used by the document has a hover signature
  the author can point to.
