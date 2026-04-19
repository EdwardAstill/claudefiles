# Tracing `af plan-exec`

Running `af plan-exec validate <plan.yaml>` flows through the following layers:

1. Shell calls `af` console script, which routes through `tools/python/src/af/main.py:_run()`.
2. `_run()` delegates to the Typer app, which matches `plan-exec` to `plan_exec_cli.py`.
3. In `plan_exec_cli.py`, the `validate_cmd` handler receives the plan path.
4. It calls `_load_or_die(plan_path)` which in turn calls `plan_exec.load(path)`. This reads the YAML file from disk, parses it with `yaml.safe_load`, and coerces the raw dicts into dataclasses via `_coerce_node` (recursive for loops).
5. `_resolve_repo_root` finds the repo root: explicit flag, else walks up for `.git`, else cwd.
6. `validate(plan, repo_root)` runs a series of checks: unique IDs, depends_on resolution, cycle detection (Kahn's algorithm), type-specific fields (reviewer, prompt, loop items/from, max_parallel), on_fail enum, files.create must not exist, files.modify must exist.
7. If errors, they're printed and the command exits 1. Otherwise prints "OK" and exits 0.

Other subcommands:

- `list` calls `toposort(plan)` and prints each node with its state.
- `next` loads the state file and returns `ready_nodes` as JSON lines.
- `mark` updates state file.
- `reset` wipes the state file.
- `status` prints a count summary.

State is persisted at `<plan>.yaml.state.json` as JSON.

Fork points: `reset` has a confirmation prompt unless `--yes`. `repo_root` resolution has three branches.

## Where it stops

Note that the current code does NOT dispatch to skills — the module docstring of `plan_exec_cli.py` says dispatch is the job of the `subagent-driven-development` skill in a later phase. So `af plan-exec` is a validator and state tracker, and the "execution" in a full sense is driven externally by reading `af plan-exec next` and calling `af plan-exec mark`.

External calls: filesystem reads and writes only. No network, no subprocess.
