---
name: python-expert
description: >
  Use when writing, reviewing, or debugging Python with attention to the
  real project toolchain: pyright LSP diagnostics, uv packaging, ruff
  lint/format, pytest conventions. Trigger phrases: "write this in
  Python", "add type hints to X", "pyright is complaining", "set up uv
  for this project", "add a ruff rule", "write pytest tests for this",
  "fix the mypy error", "parametrize this test", "convert this to use
  async", "the import is not resolving in pyright". Covers idiomatic
  typed Python, pytest shape, and live LSP introspection via pyright.
  Do NOT use for library/framework API lookup (use docs-agent /
  context7), database work that happens to be in Python (use
  database-expert), or algorithmic complexity questions (use
  dsa-expert).
includes:
  - python/pyright
  - python/uv
  - python/ruff
---

# Python Expert

Deep Python knowledge — idiomatic patterns, type system, toolchain, and live
LSP introspection. Uses pyright for type analysis, uv for packaging, and ruff
for lint/format. Those three tool chapters live in shared fragments (see the
`## Shared Conventions` block at the bottom); this file is for Python-specific
patterns, testing shape, and anti-patterns.

## Documentation

- **Package docs:** context7 MCP — resolve library ID then fetch current docs
- **Stdlib:** docs.python.org — fetch directly with WebFetch if context7 doesn't have it
- **Version check:** `af versions --write` reads `pyproject.toml` / `requirements.txt`

Always verify the installed version before fetching docs — APIs change between minor versions.

## Toolchain at a glance

| Tool       | Purpose                                | Covered in fragment    |
|------------|----------------------------------------|------------------------|
| `uv`       | Package manager, venvs, tool runner    | `python/uv`            |
| `ruff`     | Linter and formatter                   | `python/ruff`          |
| `pyright`  | Type checker and LSP                   | `python/pyright`       |
| `pytest`   | Test runner                            | see "Testing" below    |
| `mypy`     | Alternative type checker               | inline, project choice |

## Idiomatic Patterns

**Type hints** — always add them, they make pyright useful:
```python
def process(items: list[str]) -> dict[str, int]:
    ...
```

**Virtual envs** — use uv, never system pip (see `python/uv` fragment for
the full workflow).

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
