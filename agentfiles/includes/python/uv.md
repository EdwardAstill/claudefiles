---
name: python/uv
---

# uv — Package Manager and Runner

`uv` is the only Python package manager and runner we use. Never touch
system `pip`, never activate venvs by hand — `uv run` does the right
thing based on `pyproject.toml` and the lockfile.

## Day-to-day commands

```bash
uv init my-project              # pyproject.toml + .python-version + .venv
uv add requests fastapi         # runtime deps
uv add --dev pytest ruff pyright # dev-only deps
uv remove requests              # drop a dep
uv sync                         # install everything from the lockfile
uv lock                         # refresh the lockfile (no install)
uv run python main.py           # run in the project venv
uv run pytest                   # same, for the test runner
```

Rule of thumb: if you'd type `python` or `pytest`, type `uv run python`
or `uv run pytest` instead. This guarantees the correct interpreter and
packages without sourcing any activate script.

## Lockfile policy

- **Always commit `uv.lock`.** It pins every transitive dep to an exact
  version + hash. Reviewers need it to reproduce.
- **Install with `uv sync --frozen` in CI.** This fails loud if the lock
  drifts from `pyproject.toml`.
- **Never `uv lock --upgrade` as part of an unrelated change.** Lock
  churn drowns real diffs. Bump versions in a dedicated commit.

## Global tools vs project deps

```bash
uv tool install ruff            # installs in ~/.local/share/uv/tools
uvx ruff check .                # run a tool without installing first
uv tool list
uv tool upgrade ruff
```

Anything the skill itself calls from PATH (ruff, pyright via `uvx`) can
be a global tool. Anything that ships with the project under test is a
project dep.

## Python version pinning

`.python-version` (created by `uv init`) pins the interpreter. If you
need a specific minor version:

```bash
uv python install 3.12
uv python pin 3.12              # writes .python-version
```

CI should respect the pinned version — `uv` will download a matching
interpreter if needed, so "works on my machine" is mostly gone.

## Scripts

For single-file tools, inline deps skip the pyproject.toml:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx", "typer"]
# ///

import httpx
import typer
```

Run with `uv run script.py` — it builds a throwaway venv from the
script's inline metadata. Great for one-off utilities in `tools/` that
don't deserve a full package.

## Anti-patterns

- `pip install` into the system or the project venv.
- Running `python main.py` directly without `uv run` — you'll hit the
  wrong interpreter half the time.
- Gitignoring `uv.lock` because "it's noisy". Commit it.
- Mixing `uv` and `poetry` / `pdm` in one project. Pick one.
