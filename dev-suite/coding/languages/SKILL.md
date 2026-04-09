---
name: languages
description: >
  Category dispatcher for language-specific expertise. Use when deep knowledge
  of a specific language is needed — type system, idiomatic patterns, LSP
  introspection, toolchain, or documentation lookup. Routes to python-expert,
  typescript-expert, rust-expert, or typst-expert based on the language in use.
---

# Languages

Routes to the right language expert based on the language being worked in.

## Sub-skills

| Skill | Use when |
|-------|----------|
| `python-expert` | Python — type hints, uv/pip, ruff, pytest, async, pyright LSP |
| `typescript-expert` | TypeScript/JavaScript — strict types, bun/npm, biome, ts-language-server LSP |
| `rust-expert` | Rust — ownership, cargo, clippy, rustfmt, rust-analyzer LSP |
| `typst-expert` | Typst — document markup, packages, compile/watch, tinymist LSP |
