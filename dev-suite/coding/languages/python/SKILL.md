---
name: python-expert
description: >
  Python language expert. Use when writing, debugging, or reviewing Python code.
  Covers type hints, async patterns, packaging with uv, linting with ruff,
  testing with pytest, and live code introspection via the pyright LSP.
---

# Python Expert

Deep Python knowledge — idiomatic patterns, type system, toolchain, and live
LSP introspection. Uses pyright for type analysis and context7 for package docs.

## LSP — pyright

Always run LSP diagnostics before suggesting fixes. Pyright catches type errors,
undefined names, and incorrect signatures that reading code alone can miss.

```
LSP: hover       — type of any expression
LSP: diagnostics — type errors, undefined references
LSP: definition  — jump to source of any symbol
LSP: references  — find all usages
```

Install: `bun install -g pyright`

For richer completions and refactoring, `pylsp` is an alternative:
`uv tool install python-lsp-server`

## Documentation

- **Package docs:** context7 MCP — resolve library ID then fetch current docs
- **Stdlib:** docs.python.org — fetch directly with WebFetch if context7 doesn't have it
- **Version check:** `cf-versions --write` reads `pyproject.toml` / `requirements.txt`

Always verify the installed version before fetching docs — APIs change between minor versions.

## Toolchain

| Tool | Purpose | Command |
|------|---------|---------|
| `uv` | Package manager, virtual envs, tool runner | `uv add <pkg>`, `uv run <cmd>` |
| `ruff` | Linter and formatter (replaces black + flake8) | `ruff check .`, `ruff format .` |
| `pytest` | Test runner | `uv run pytest` |
| `pyright` | Type checker | `pyright` |
| `mypy` | Alternative type checker | `uv run mypy .` |

## Idiomatic Patterns

**Type hints** — always add them, they make pyright useful:
```python
def process(items: list[str]) -> dict[str, int]:
    ...
```

**Virtual envs** — use uv, never system pip:
```bash
uv init my-project
uv add requests
uv run python main.py
```

**Async** — prefer `asyncio` with `async`/`await`; use `anyio` for library code that shouldn't pin to a specific event loop.

**Error handling** — use specific exception types; avoid bare `except:`.

**Imports** — standard library → third party → local, separated by blank lines. `ruff` enforces this automatically.

## Anti-patterns

| Anti-pattern | Instead |
|-------------|---------|
| Mutable default arguments `def f(x=[])` | Use `None` and set inside |
| `except Exception` swallowing errors | Catch specific types, log or re-raise |
| `os.path` for path manipulation | Use `pathlib.Path` |
| `print()` for debugging | Use `logging` or a debugger |
| Ignoring type errors | Fix them — they're real bugs |

## Outputs

- Type-checked, ruff-clean code
- LSP diagnostics report for any file reviewed
- `uv`-based project setup if scaffolding is needed
