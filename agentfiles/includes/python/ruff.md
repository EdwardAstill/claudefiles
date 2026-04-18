---
name: python/ruff
---

# Ruff — Lint and Format

Ruff is the single linter + formatter for Python work in this suite. It
replaces `black`, `isort`, and `flake8`. Always run it before committing —
the cost is seconds, the payoff is zero style review.

## Two commands you need

```bash
uv run ruff check .             # lint
uv run ruff check . --fix       # lint + auto-fix safe rules
uv run ruff format .            # format
```

Run `check --fix` before `format` — auto-fixes can change the AST in ways
that matter to the formatter.

## Recommended rule set

`[tool.ruff.lint]` in `pyproject.toml`:

```toml
[tool.ruff.lint]
select = [
  "E",    # pycodestyle
  "F",    # pyflakes
  "I",    # isort
  "B",    # flake8-bugbear (real bug patterns)
  "UP",   # pyupgrade — use modern syntax
  "SIM",  # flake8-simplify
  "RUF",  # ruff-specific
]
ignore = [
  "E501",  # line length — let the formatter handle it
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["B011"]           # allow `assert False` in tests

[tool.ruff.format]
quote-style = "double"
docstring-code-format = true
```

## Rules we always follow

- **Imports grouped** stdlib → third-party → local, separated by blank
  lines. Ruff's `I` rules enforce this; don't hand-sort imports.
- **No unused imports or variables.** Fail CI on these; don't leave them
  for later.
- **Prefer `pathlib` over `os.path`** (`PTH` rules). Ruff will flag the
  easy wins.
- **Use f-strings over `%` or `.format()`** (`UP032`). Stop writing old
  formatting in new code.
- **Explicit re-exports.** `__all__` wins over `from x import *` — and
  ruff's `F401` rule disappears once the re-export is declared.

## Pre-commit wiring

Add to `.pre-commit-config.yaml` so contributors can't bypass:

```yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.6.9
  hooks:
    - id: ruff
      args: [--fix]
    - id: ruff-format
```

## Anti-patterns around ruff

- Disabling rules globally because one file breaks them. Use
  `# noqa: RULE` on the offending line, or add a `per-file-ignores` entry.
- Committing without running `ruff format`. Make it a pre-commit hook.
- Blanket `--fix --unsafe-fixes` — unsafe fixes are unsafe by definition.
  Apply them manually, read the diff.
