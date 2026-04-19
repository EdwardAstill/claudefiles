# Architecture of the `af` CLI

The `af` tool is a Typer-based command-line utility under `tools/python/src/af/`. It follows a dispatcher + subcommand pattern.

## Entry point and dispatch

`main.py` is the entry point. It defines a `_SUBCOMMANDS` list mapping each subcommand name to its module name, and a `_register()` function that dynamically imports each module and attaches its Typer app as a sub-app. There is also a `_run()` function that intercepts `install` and `research` because they don't use the Typer sub-app convention (install uses click, research uses argparse).

So the flow is: `af <cmd>` → `_run()` → either the intercept path (install/research) or `app()` → the registered sub-Typer for `<cmd>`.

## Subcommand modules

Each subcommand is its own file: `context.py`, `status.py`, `init.py`, `install.py`, `audit.py`, `plan_exec_cli.py`, `hub.py`, `learn.py`, `log.py`, `metrics.py`, `note.py`, `read.py`, `research.py`, `mode.py`, `preview.py`, `agents.py`, `index.py`, `tree.py`, `worktree.py`, etc.

Each exposes `app = typer.Typer(...)` and a callback or one or more `@app.command` functions. The module itself handles argument parsing (via Typer) and calls into domain logic.

## Domain logic

Some modules hold significant logic beyond CLI wiring:

- `plan_exec.py` — loader, validator, toposort, and state file for plan YAML files. Used by `plan_exec_cli.py`.
- `includes.py` — shared fragment expansion for SKILL.md files.
- `archetype.py`, `caveman.py`, `agent_knowledge.py`, `skill_find.py` — each their own domain.

## Infrastructure

- `lib.py` — shared helpers like `git_root`, `bus`, `ensure_bus`.
- `repo.py` — git helpers.
- `data/` — static assets.

## Adding a new subcommand

To add `af foo`:

1. Create `tools/python/src/af/foo.py` with a module-level `app = typer.Typer()`.
2. Add `("foo", "foo")` to `_SUBCOMMANDS` in `main.py`.
3. Add `[skills.foo]` or `[cli.foo]` to `manifest.toml` if it needs to be distributed.
4. Write tests in `tools/python/tests/`.

The typer app in your module will be attached automatically by `_register()` when main.py is imported.
