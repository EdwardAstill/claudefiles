# Architecture of the `af` CLI

## Step 1 — Orient

**Project fingerprint:** `af` is a Typer-based Python CLI shipped as a uv tool, installed from `tools/python/` (per `manifest.toml` → `[cli.af]`). Package layout: `tools/python/src/af/` with ~45 module files. Entry point is `af.main:_run` via the console script.

Top-level signal from `main.py`: a `_SUBCOMMANDS` tuple list (40+ entries) and a `_register()` function that imports each module and attaches its `app` as a Typer sub-app. Two commands (`install`, `research`) are intercepted in `_run()` because they use click / argparse instead of the Typer sub-app pattern.

## Step 2 — Architecture Layers

| Layer | Responsibility | Files |
|-------|----------------|-------|
| **1. Entry & Dispatch** | Parse argv, route to subcommand | `main.py`, `__init__.py` |
| **2. Subcommand Shell** | Per-command Typer app, argument parsing | `context.py`, `status.py`, `init.py`, `audit.py`, `plan_exec_cli.py`, `hub.py`, `mode.py`, `learn.py`, `log.py`, `note.py`, `read.py`, `index.py`, `metrics.py`, `preview.py`, `agents.py`, `tree.py`, `worktree.py`, `include.py` (→ `includes.py`), `skill_find.py`, `skill_usage.py`, `test_skill.py`, `archetype.py`, `ak` (→ `agent_knowledge.py`), `caveman.py`, `search.py`, `tools_cmd.py`, `secrets.py`, `screenshot.py`, `versions.py`, `terminal.py`, `webscraper.py`, `youtube.py`, `setup.py`, `plan_scaffold.py` |
| **3. Domain / Core Logic** | Encode actual behavior (not CLI wiring) | `plan_exec.py`, `includes.py`, `agent_knowledge.py`, `archetype.py`, `caveman.py`, `skill_find.py` |
| **4. Infrastructure / I/O** | Filesystem, git, shared utilities | `lib.py`, `repo.py`, `log.py`, `data/` |
| **5. Installer (special)** | Read manifest, install skills/hooks/CLI tools into `~/.claude/` | `install.py` (click-based, not Typer) |

### What each layer receives and returns

- **Entry & Dispatch:** in = argv (list[str]); out = exit code. `_run()` holds the install/research intercepts and otherwise calls Typer's `app()`.
- **Subcommand Shell:** in = parsed Typer args; out = stdout text + exit code. Each module declares `app = typer.Typer(...)` and either a `@app.callback` or one or more `@app.command` functions. No shared base class — convention-based.
- **Domain / Core:** in = Path / dataclass / string inputs; out = domain objects (e.g., `Plan`, `Node`, expanded SKILL body) or typed error lists. Example: `plan_exec.load(path) -> Plan`, `plan_exec.validate(plan, repo_root) -> list[str]`.
- **Infrastructure / I/O:** in = path / name; out = filesystem or git state. `lib.git_root()`, `lib.bus()`, `lib.ensure_bus()`.
- **Installer:** in = manifest.toml + `agentfiles/` tree; out = populated `~/.claude/skills/`, `~/.claude/hooks/`, merged settings.json. Invoked only via `_run()`'s intercept because it uses click and needs argv passthrough.

## Step 3 — Execution Path (typical `af <cmd>` call)

1. Shell invokes the `af` console script → `af.main:_run`.
2. `_run()` checks argv[1]: if `install`, imports `af.install.install_cmd` and calls it with the rest of argv; if `research`, imports `af.research.cli` and calls it; else calls Typer's `app()`.
3. Typer matches the subcommand against the registered sub-apps (wired during `_register()`).
4. The sub-app's callback or command handler runs, parses its own flags/args.
5. Handler calls into domain layer for real work (e.g., `plan_exec_cli.validate_cmd` → `plan_exec.load` → `plan_exec.validate`).
6. Domain layer calls `lib.git_root()` / direct filesystem I/O as needed.
7. Result is echoed via `typer.echo`; exit code via `typer.Exit` or implicit 0.

Fork points: install/research vs Typer path is the only one at the dispatch level.

## Step 4 — Key Abstractions

- **`_SUBCOMMANDS` registry** (`main.py`): the single source of truth for wiring. Any new command needs a tuple here.
- **Per-module `app = typer.Typer(...)`**: the contract every subcommand module satisfies. No shared base class — duck-typed against `app.add_typer`.
- **`_run()` intercept pattern** (`main.py`): the escape hatch for commands that can't conform to the Typer sub-app convention. Currently used for install (click CLI needing passthrough) and research (argparse with positional).
- **Domain functions returning dataclasses + error lists**: uniform style in `plan_exec.py` — typed `Plan`, `Node` dataclasses loaded/validated by pure functions; errors returned as `list[str]` so the CLI can render them directly.
- **`manifest.toml`** as declarative registry: while not Python code, it's the system's spine — lists every skill, CLI tool, agent, and mode the installer deploys.

## Step 5 — Mental Model Summary

1. **What it does** — one-word-per: personal CLI for installing, inspecting, and orchestrating agentfiles (skills, hooks, plans, modes) under `~/.claude/`.
2. **Architecture** — 5 layers: Entry & Dispatch (`main.py`) → Subcommand Shell (one Typer app per file) → Domain / Core (plan_exec, includes, etc.) → Infrastructure (lib, repo) → Installer (install.py, special-cased).
3. **Execution path** — argv → `_run()` → (intercept OR Typer) → subcommand handler → domain call → lib I/O → exit code.
4. **Key abstractions** — `_SUBCOMMANDS` registry, per-module Typer `app`, `_run()` intercept, domain dataclasses + error-list returns, `manifest.toml`.
5. **Where to look** — add a subcommand: new module in `af/` + entry in `_SUBCOMMANDS` + manifest entry + test. Fix install behaviour: `install.py`. Change plan semantics: `plan_exec.py`. Change fragment expansion: `includes.py`.

### When to stop

You can now answer:

- "Where would I add a new subcommand?" → new file under `af/`, add to `_SUBCOMMANDS`, optionally add to manifest.toml.
- "What would break if I renamed `main.py`?" → `af` console script points there; also `af.install` and `af.research` are imported by name in `_run()`.
- "What does `af plan-exec validate` depend on?" → `plan_exec_cli.validate_cmd` → `plan_exec.load` + `plan_exec.validate` + `lib.git_root` (via `_resolve_repo_root`).

### Pitfalls

- The Typer sub-app convention is not enforced — adding a new command without `app = typer.Typer(...)` at module level will silently be swallowed by the `ModuleNotFoundError` guard in `_register()`.
- Two commands (`install`, `research`) bypass Typer entirely. If you change `_run()`, you can break passthrough arg handling.
- `_SUBCOMMANDS` and `manifest.toml` are two separate registries — forgetting one means the command works locally but doesn't install cleanly.
