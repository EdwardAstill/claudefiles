---
name: python-expert
description: >
  Python toolchain and conventions specialist. Use when you need pyright LSP
  diagnostics, uv package management, ruff linting, or pytest patterns — the
  tooling integration and project conventions that the base model doesn't enforce.
  Not for general Python knowledge (the model already has that). Covers type hints,
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
- **Version check:** `af versions --write` reads `pyproject.toml` / `requirements.txt`

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

## Testing

**Framework:** pytest — always `uv run pytest`, never `python -m pytest` directly.

**Structure:**
```
tests/
  conftest.py         # shared fixtures
  unit/               # pure function tests, no I/O
  integration/        # tests that hit real deps (db, filesystem, network)
```

**Fixtures over setUp/tearDown:**
```python
@pytest.fixture
def db_session():
    session = create_session()
    yield session
    session.rollback()
    session.close()
```

**Parametrize for coverage:**
```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("", ""),
])
def test_upper(input, expected):
    assert input.upper() == expected
```

**Run during development:**
```bash
uv run pytest tests/unit/ -v           # unit only
uv run pytest -k "test_auth" -v        # by name pattern
uv run pytest --cov=src --cov-report=term-missing
```

## Package Management (uv)

**New project:**
```bash
uv init my-project          # creates pyproject.toml, .python-version, .venv
uv add requests fastapi     # add dependencies
uv add --dev pytest ruff    # dev-only dependencies
```

**Lock file:** `uv.lock` — always commit. Reproduces exact dependency tree.

**Run commands:**
```bash
uv run python main.py       # runs in project venv
uv run pytest               # runs pytest from project venv
uv sync                     # install all deps from lock file
```

**Global tools:**
```bash
uv tool install ruff         # install globally, not per-project
uvx ruff check .             # run without installing
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using `python` instead of `uv run` | Always `uv run python` — ensures correct venv |
| Committing without running `ruff format` | Add `uv run ruff format .` to pre-commit |
| Missing type hints on public functions | Add them — pyright can't help without them |
| `from module import *` | Always explicit imports |
| Catching `Exception` in tests | Let it propagate — don't hide failures |

## Outputs

- Type-checked, ruff-clean code
- LSP diagnostics report for any file reviewed
- `uv`-based project setup if scaffolding is needed
