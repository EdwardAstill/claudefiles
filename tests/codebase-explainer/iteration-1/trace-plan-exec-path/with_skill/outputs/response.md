# End-to-End Trace: `af plan-exec`

## Step 1 — Orient

Entry from the shell is the `af` console script (declared in `tools/python/pyproject.toml`, registered in `manifest.toml` as `[cli.af]`). It resolves to `af.main:_run`. The user invokes `af plan-exec <subcommand> <plan.yaml>`.

**Critical architectural fact to surface up front.** The module docstring of `plan_exec_cli.py` states explicitly: "This command does NOT dispatch subagents; that is the `subagent-driven-development` skill's job (Phase 2C). The CLI is a thin wrapper over `af.plan_exec` for humans and skills to drive a plan through its lifecycle." So the "end-to-end execution path" stops at the ready-node picker — downstream skill invocation is driven by a separate skill that reads `af plan-exec next` and calls back into `af plan-exec mark`. If you were expecting a subprocess fan-out inside plan_exec, there isn't one yet.

## Step 2 — Layers Touched

| Layer | Module | Role |
|-------|--------|------|
| Entry | `main.py` | Typer dispatch, `_run()` intercept |
| Subcommand shell | `plan_exec_cli.py` | Typer commands: validate, list, next, mark, reset, status |
| Domain / Core | `plan_exec.py` | Load, validate, toposort, StateFile |
| Infrastructure | stdlib (pathlib, yaml, json) | Disk I/O |

## Step 3 — Numbered Execution Path

Tracing `af plan-exec <cmd> <plan.yaml>`:

1. **`main.py:_run()`** — argv inspected. `install`/`research` are intercepted here; `plan-exec` is not, so flow falls through to `app()` (Typer).
2. **Typer routing** — `plan-exec` matches the sub-app attached during `_register()` via `app.add_typer(plan_exec_cli.app, name="plan-exec")` (wired through the `_SUBCOMMANDS` entry `("plan-exec", "plan_exec_cli")`).
3. **`plan_exec_cli.py` — one of six leaf commands fires:** `validate_cmd`, `list_cmd`, `next_cmd`, `mark_cmd`, `reset_cmd`, `status_cmd`. Typer has already validated the `plan_yaml: Path` argument exists and is readable.
4. **`plan_exec_cli._load_or_die(plan_yaml)`** — wraps `plan_exec.load`. Prints error to stderr and exits 1 on `PlanParseError`.
5. **`plan_exec.load(path)`** — external call: **filesystem read** via `path.read_text()`. Parses with `yaml.safe_load`. If the top-level is not a mapping or `version`/`nodes` are missing, raises `PlanParseError`. Builds a `PlanMeta` and then walks `nodes` calling…
6. **`plan_exec._coerce_node(raw, where)`** — recursive data transform. Raw dicts → typed dataclasses (`ImplementNode`, `VerifyNode`, `ReviewNode`, `PauseNode`, `LoopNode`). Loop bodies recurse. Validates node type is in `VALID_NODE_TYPES` = {implement, review, verify, pause, loop}. Returns a `Plan` dataclass.
7. **(validate path only) `plan_exec_cli._resolve_repo_root`** — three-way resolution: explicit `--repo-root` flag > walk parents of plan path for `.git` > cwd. No filesystem writes, reads stat() on ancestors.
8. **(validate path only) `plan_exec.validate(plan, repo_root)`** — returns `list[str]` of error messages. Seven invariants checked:
   - (a) Unique ids across top-level + loop bodies (`_all_ids` walks loop.body).
   - (b) `depends_on` references resolve to top-level ids.
   - (c) Cycle detection via **Kahn's algorithm** on `in_degree` / `adj` maps — in_degree is computed from depends_on, queue is sorted to give deterministic tie-breaking.
   - (d) Type-specific required fields: `review.reviewer` must be in {spec, code_quality}; `pause.prompt` non-empty; `loop` has `items` XOR `from` and `max_parallel ∈ [1, 10]` (cap `MAX_PARALLEL_CAP`) and non-empty `body`.
   - (e) `on_fail` in {retry, escalate, pause} (enum `VALID_ON_FAIL`).
   - (f) `files.create` paths must NOT exist on disk (**filesystem read** — `(repo_root / p).resolve().exists()`).
   - (g) `files.modify` paths MUST exist on disk (**filesystem read** — same).
9. **(list path) `plan_exec.toposort(plan)`** — Kahn's algorithm again but now builds output order. Stable: within a ready-set level, sorted alphabetically by id. Raises `ValueError` on cycle (validate should have surfaced it first).
10. **(mark / next / status / list path) `plan_exec.StateFile.load(<plan>.yaml.state.json)`** — **filesystem read** (optional — if missing, empty state). Parses JSON; each value must be in `VALID_STATES` = {pending, running, done, failed} else `PlanParseError`.
11. **(mark path) `StateFile.mark(node_id, status)`** — validates status enum, updates the in-memory dict, immediately persists via `save()` → **filesystem write** on `<plan>.yaml.state.json` (`json.dumps(..., indent=2, sort_keys=True)`).
12. **(next path) `StateFile.ready_nodes(plan)`** — calls `toposort` again, then filters: self not in recorded states (or explicitly `pending`) AND all `depends_on` are `done`. Returns `list[Node]`.
13. **(next path) `next_cmd` emits one `json.dumps({"id", "type", "description"})` line per ready node → stdout.** This is the handoff. The driving skill (subagent-driven-development, phase 2C) is expected to consume the JSON lines, invoke one subagent per node, then call back into `af plan-exec mark <id> done` (a fresh subprocess spawned by the skill, **not** by plan_exec).
14. **(reset path) `reset_cmd`** — optional `typer.confirm` prompt unless `--yes`. Then `StateFile.reset(path)` → `path.unlink()` (**filesystem write**).
15. Exit code bubbles back through `plan_exec_cli` → Typer → `main._run()` → shell.

## Step 4 — Key Abstractions in Play

- **`Plan` dataclass** (`plan_exec.py:97`) — the typed domain object. All downstream logic consumes `Plan`, never raw YAML.
- **`Node` union type** — `ImplementNode | VerifyNode | ReviewNode | PauseNode | LoopNode`. Type-specific validation uses `isinstance` checks.
- **`StateFile`** — stateful companion to the Plan. Immutable YAML + mutable sidecar JSON. The path convention is `<plan>.yaml.state.json` (helper `_state_path_for`). Supports `load`, `save`, `mark`, `reset`, `ready_nodes`, `status_summary`.
- **Error-list-return pattern** — `validate` returns `list[str]` rather than raising. CLI layer iterates and prints. Keeps domain pure.
- **Kahn's algorithm used twice** — once in validate (cycle detection with `|visited| == |nodes|` check), once in toposort (produces the order). Deliberately deterministic (sorted within level).

## Step 5 — Mental Model: Forks and Externalities

### Fork points in the path

1. **Command verb** — six leaves (validate | list | next | mark | reset | status) pick different terminal functions. All share load + StateFile.load upstream.
2. **Repo root resolution** — `_resolve_repo_root`: explicit flag > ancestor `.git` > cwd.
3. **Interactive vs non-interactive reset** — `typer.confirm` unless `--yes`.
4. **State-file presence** — `StateFile.load` returns an empty StateFile if the sidecar doesn't exist; otherwise it parses.
5. **Cycle short-circuit** — `toposort` raises `ValueError`; `validate` instead catches the condition by comparing visited count and returns an error string. They disagree on surface — always run validate first.

### External calls (by category)

- **Filesystem read**: plan YAML (once), state JSON (once per command), file existence stat for `files.create` / `files.modify` checks (every entry during validate).
- **Filesystem write**: state JSON on `mark`; state JSON unlinked on `reset`.
- **No network, no subprocess, no git** inside plan_exec. Git only enters via `_resolve_repo_root`'s stat check for `.git` (a directory test, not a git call).

### Path that does NOT run here (but is one layer up)

- Skill dispatch: the driving skill fans out per ready node, probably via the Agent tool / subprocess to a subagent; it is the one that spawns work. plan_exec only advises.
- Hook observation: `hooks/skill-logger.py` PostToolUse sees the tool calls from both the driving skill and any subagent it spawns, and logs them to `~/.claude/logs/sessions/` and `~/.claude/logs/agentfiles.jsonl`. Orthogonal to plan_exec's path — they meet only in the log pipeline.

### When to stop

You can now answer:

- "What does `af plan-exec mark N done` touch?" → `plan_exec_cli.mark_cmd` → `plan_exec.load` → `StateFile.load` → `StateFile.mark` → filesystem write `<plan>.yaml.state.json`.
- "Where would cycle detection break?" → `plan_exec.validate` step (c) — Kahn's with visited-count comparison; `toposort` also detects but raises instead of error-listing.
- "What file changes if I resume a plan?" → just `<plan>.yaml.state.json`; the plan YAML itself is never modified by any command.
