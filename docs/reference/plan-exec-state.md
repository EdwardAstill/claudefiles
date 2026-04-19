# Plan-exec state file — scoping rules

Reference for `af plan-exec mark` and the sidecar `<plan>.yaml.state.json`
file it mutates. Settles open questions from the shipped design plan
at `docs/plans/archive/2026-04-18-plan-yaml-schema.md`.

## Node id namespace

**Single global namespace.** Every node id in a plan — top-level nodes
and nodes nested inside a `loop.body` — shares one namespace. The
validator rejects duplicates across the whole plan.

Rationale: simpler mental model, no `"parent-loop.body-node"` disambiguation,
and the validator can treat ids as a flat set. Loop bodies are a structural
grouping, not a scoping boundary.

## `af plan-exec mark` — which ids are accepted?

`mark` accepts **any id that exists anywhere in the plan**, including ids
that live inside a `LoopNode.body`. Current behavior (`tools/python/src/af/plan_exec_cli.py:71`
`_all_node_ids()` walks `plan.nodes` *and* each node's `body`, returning a
flat set).

This is the intentional design. It gives two things:

- **Manual override for partial loop bodies.** If a user runs a loop body
  step out-of-band and wants the state file to reflect reality, `mark`
  lets them pin it `done` without having to run the whole loop through
  the pipeline again.
- **Symmetry with top-level marking.** Top-level and body nodes are
  marked through the same interface; no special-casing by position in
  the tree.

Not scoped to the parent loop. Not per-iteration.

## What the state file does **not** track

- Per-iteration state inside a loop. The state file records a single
  status for each body node id. If a body runs N iterations over
  `loop.items`, those iterations share one status entry. The runtime
  (currently `subagent-driven-development`) is responsible for
  per-iteration bookkeeping if it needs it.
- Transitions. `mark` sets the status; it doesn't validate that the
  transition is legal (e.g. `done` → `running`). That guard belongs in
  the caller.
- History. The file is a flat `{id: status}` map. No timestamps, no
  prior-status log.

Adding any of the above is a forward design change, not a spec
clarification. Items surface as `[speculative]` in `NEXT_STEPS.md` §3 if
needed.

## Implications

1. **Loop body ids must be globally unique.** Plan authors can't reuse
   the same id across two loops in one plan. The validator enforces this.
2. **`mark <body-id>` does not implicitly mark the parent `loop` node.**
   The two are independent cells in the state map. A loop finishes only
   when every body id is `done` AND the loop's own top-level node is
   `done`.
3. **`reset` wipes the whole file.** Per-node reset is not supported;
   use `mark <id> pending` to reset a single node.

## Related code

- `plan_exec.py:77` — `LoopNode` dataclass with `body: list[Node]`
- `plan_exec.py:463` — `StateFile.mark()`
- `plan_exec_cli.py:71` — `_all_node_ids()` (the set `mark` validates against)
- `plan_exec_cli.py:149` — `mark_cmd` CLI entrypoint

Tests covering this behavior live in `tools/python/tests/test_plan_exec_cli.py`
(`test_mark_unknown_node_fails` and friends).
