---
name: python/pyright
---

# Pyright — LSP Workflow

Pyright is the primary type checker and language server for Python skills in
this suite. Always run diagnostics before suggesting fixes — reading code
alone misses type errors, undefined names, and incorrect signatures.

## LSP verbs (prefer over CLI)

```
LSP: hover       — inferred type of any expression
LSP: diagnostics — type errors, undefined references, unreachable code
LSP: definition  — jump to source of any symbol
LSP: references  — find all usages across the project
LSP: rename      — project-wide safe rename
```

Reach for the LSP before `pyright` on the command line. The LSP gives
incremental, on-demand answers; the CLI is for CI-style whole-project sweeps.

## Install / invoke

```bash
bun install -g pyright          # per `manifest.toml` → [cli.pyright]
pyright                         # full-project check
pyright path/to/file.py         # single-file check
pyright --outputjson            # machine-readable diagnostics
```

For richer completions and refactoring, `pylsp` is an alternative:

```bash
uv tool install python-lsp-server
```

## Common config

`pyright` reads `[tool.pyright]` from `pyproject.toml`. Sensible defaults:

```toml
[tool.pyright]
include = ["src", "tests"]
venvPath = "."
venv = ".venv"
reportMissingImports = "warning"
reportMissingTypeStubs = "none"
strict = ["src/af/**"]
```

- `venvPath` + `venv` make pyright pick up the uv-managed `.venv` without
  sourcing `activate` first.
- Start with `basic` mode and promote specific paths to `strict` once they
  are clean. Never silence diagnostics with `# type: ignore` without a
  short reason after — `# type: ignore[reportGeneralTypeIssues] (see PR #123)`.

## Interpreting diagnostics

- **`reportGeneralTypeIssues`** — real type error, fix the signature or cast.
- **`reportUnknownMemberType`** — usually a missing stub; add one or pin the
  dep to a version that ships types.
- **`reportMissingImports`** — venv mismatch; check `venvPath` / `venv`.
- **`reportOptionalMemberAccess`** — narrow the `Optional` with an `if x is
  not None` guard, not `assert`.

If diagnostics disagree with runtime behaviour, trust pyright first — the
runtime is almost always the thing that's wrong.

## Outputs expected from skills using pyright

- A pyright diagnostics report for any file reviewed.
- No new `# type: ignore` unless the reason is written next to it.
- Strict-mode clean code for any file under a `strict = [...]` glob.
