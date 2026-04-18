# Plan YAML Schema

**Status:** Phase 1 complete — core loader, dataclasses, and DAG validator
landed at `tools/python/src/af/plan_exec.py` with 18 tests in
`tools/python/tests/test_plan_exec.py`. No CLI surface yet; module is
importable but not registered in `af.main`.

**Remaining for Phase 2:**

- Typer `app` + subcommands (`validate`, `next`, `mark`, `run`) and register
  on `af.main`.
- State mutation (Phase 2 Agent A owns `af plan-exec mark`).
- Dispatch logic lives in the `subagent-driven-development` skill, not the
  CLI — wire the skill to call the loader/validator once Phase 2 ships.
- Update `writing-plans` skill to emit the YAML sidecar alongside the prose
  plan (see §6 Migration).

**Phase 1 notes / schema ambiguities flagged for Phase 2:**

- **YAML parser choice.** Spec §5 names `ruamel.yaml`; Phase 1 used
  `PyYAML` (`pyyaml>=6.0`) per the Phase 1 task brief. Revisit if round-trip
  preservation (comment/line-number fidelity) becomes a requirement for
  error messages or `af plan-scaffold`.
- **Loop body ids and duplicates.** The current validator treats duplicate
  ids as global (top-level + loop body ids share one namespace). Spec is
  silent; reconsider if you want per-loop id scoping.
- **Loop body `depends_on`.** Validator only resolves top-level
  `depends_on` against top-level ids. Whether inner body nodes can
  `depends_on` each other (likely yes) or reach out of the loop (likely
  no) is not nailed down in the spec.
- **`${item}` templating.** Recognised syntactically in fixtures; not
  expanded, not validated, not enforced as the only templating primitive.
  Phase 2 dispatcher needs to define substitution semantics.
- **`files.test`.** Parsed but not validated (neither create-if-missing
  nor must-exist makes obvious sense for tests). Spec doesn't say.
- **`verify` node type.** Coerced into a dataclass but the spec table
  elides type-specific requirements — currently permissive (treated like
  `implement` minus type name). Decide if a `verify`-type node must have a
  non-empty `verify:` list.
- **`repo_root` for filesystem invariants.** `validate()` accepts an
  explicit `repo_root` so tests can sandbox. Phase 2 CLI will need a
  policy (plan file dir? `git rev-parse --show-toplevel`? CWD?).

**Inspired by:** `coleam00/Archon` — see `research/projects/methodology-and-workflows/coleam00-archon.md`

## 1. Goal

Define a machine-readable YAML sidecar that mirrors the human prose plan, so `subagent-driven-development` dispatches from a validated DAG instead of re-parsing markdown bullets.

## 2. Current state

`writing-plans` produces `docs/plans/YYYY-MM-DD-<name>.md`. Plans have a prose header (Goal, Architecture, Tech Stack), a file-structure table, then `### Task N` sections with `- [ ]` checkbox steps embedded with code fences, shell commands, and expected output.

`subagent-driven-development` extracts tasks by pattern-matching the `### Task N:` heading and `- [ ] **Step k:**` rhythm. No explicit `depends_on` — ordering is positional. Human gates absent. Loop bodies (`Batch Loop Mode`) live in the executor's head, not the plan.

**Where it breaks:** rename a heading, lose a checkbox, split a task across two `###` blocks — the mental parser drifts. Nothing validates that Task 3 references files Task 1 promised to create.

## 3. YAML schema

Sidecar file `docs/plans/<plan-slug>.yaml` with top-level `version`, `plan`, `nodes`. Every node:

| Field | Required | Notes |
|---|---|---|
| `id` | yes | snake_case, unique within plan |
| `type` | yes | `implement` \| `review` \| `verify` \| `pause` \| `loop` |
| `depends_on` | no | list of node ids; empty means roots |
| `description` | yes | one-line intent (full prose lives in .md) |
| `prose_ref` | no | anchor in the .md, e.g. `task-3-step-2` |
| `files` | no | `create:` / `modify:` / `test:` — mirrors the markdown table |
| `verify` | no | list of shell commands that must exit 0 |
| `on_fail` | no | `retry` \| `escalate` \| `pause` (default `escalate`) |

Type-specific fields: `review.reviewer` (`spec` or `code_quality`); `pause.prompt`; `loop.items` (list or `from: <path>`), `loop.body` (inline node subgraph), `loop.until` (optional predicate), `loop.max_parallel` (default 1, cap 10).

### Worked example — add `af session resume`

```yaml
version: 1
plan:
  slug: af-session-resume
  prose: docs/plans/2026-04-18-af-session-resume.md
  goal: Add `af session resume` that reopens the last session's scratchpad.

nodes:
  - id: spec_contract
    type: implement
    description: Pin the contract — flags, exit codes, output shape.
    files:
      create: [tools/python/src/af/session_resume.py]
      test:   [tools/python/tests/test_session_resume.py]
    verify:
      - uv run --directory tools/python pytest tests/test_session_resume.py -k contract -v

  - id: cli_wiring
    type: implement
    depends_on: [spec_contract]
    description: Register `resume` on the session Typer app.
    files:
      modify: [tools/python/src/af/session.py]
    verify:
      - uv run --directory tools/python af session resume --help

  - id: spec_review
    type: review
    reviewer: spec
    depends_on: [cli_wiring]
    description: Does the impl match the spec doc (no extra flags)?
    on_fail: retry

  - id: human_gate_ux
    type: pause
    depends_on: [spec_review]
    prompt: >
      Copy of `af session resume --help` is above. Approve wording
      before I write user-facing docs?

  - id: docs_per_surface
    type: loop
    depends_on: [human_gate_ux]
    description: Mention `resume` in each session doc.
    items:
      - docs/wiki/af-session.md
      - README.md
      - AGENTS.md
    max_parallel: 3
    body:
      - id: update_doc
        type: implement
        description: Add one paragraph on `resume` to ${item}.
        verify:
          - uv run --directory tools/python af check ${item}

  - id: quality_review
    type: review
    reviewer: code_quality
    depends_on: [docs_per_surface]
    verify:
      - uv run --directory tools/python pytest
      - uv run --directory tools/python ruff check src tests
```

`${item}` is the only templating primitive — a loop binding. No general Jinja; keep it boring.

## 4. Relationship to the prose plan

**Sidecar file**, not embedded. Two files: `2026-04-18-foo.md` beside `2026-04-18-foo.yaml`.

Reasoning: markdown plans are already dense with code fences and shell output. Embedding YAML inside forces the parser to strip markdown and makes both formats harder to read. A sidecar keeps each pristine, lets `af check` parse YAML with a plain loader, and lets editors apply YAML-aware tooling. Cross-link via `prose:` in the YAML and `**Machine plan:** 2026-04-18-foo.yaml` in the markdown header.

## 5. Tooling — `af plan-exec`

**Minimal v1 (`af plan-exec <plan.yaml>`):**

1. **Loader** — parse with `ruamel.yaml`, coerce into typed dataclasses (`Node`, `LoopNode`, `PauseNode`).
2. **Validator** — unique ids, `depends_on` resolves, no cycles, type-specific required fields, `files.create` paths don't exist, `files.modify` paths do. Fail fast with line numbers.
3. **Dispatcher** — topological walk. `implement` → implementer subagent with `description` + referenced prose; `review` → spec or quality reviewer; `verify` → run shell commands locally; `pause` → print prompt, block on stdin; `loop` → fresh subagent per item (cap `max_parallel`), merge results.
4. **State file** — `<plan>.state.json` with node status (`pending` / `running` / `done` / `failed`). Re-runs skip `done` nodes.

**Defer:** DAG dry-run renderer, resume from arbitrary node, DOT export, multi-surface dispatch (Archon territory — skip).

## 6. Migration

YAML is opt-in; existing prose plans keep working. New plans: `writing-plans` emits both files as its final step. In-flight old plans: `af plan-scaffold <plan.md>` greps `### Task` headings and emits a YAML skeleton; the author fills in `depends_on`, `verify`, and gate placements. Completed plans stay as-is — no auto-migration.

## 7. Scope limits — DON'T write YAML for

- **Single-task bugfixes.** One commit, one verify command, no gates — prose is enough.
- **Simple refactors** of one file with a single passing test suite.
- **Research / exploration plans** whose output is a document, not code.
- **Plans short enough to hold in one screen** (under ~3 tasks, no loops, no human gates).

Rule of thumb: if `subagent-driven-development` would dispatch more than three subagents or has a human checkpoint, write the YAML. Otherwise the prose plan alone is fine.

## 8. Risks and open questions

- **Drift between .md and .yaml.** Mitigation: `af check` verifies every `prose_ref` resolves to a real anchor and every `### Task N` has a matching `implement` node. Hard-fail CI on mismatch.
- **YAML fatigue.** Archon users resented the verbosity. Mitigation: flat schema, most fields optional, `prose_ref` escape hatch over duplication.
- **Loop isolation.** "Fresh context" is easy to claim, hard to enforce with shared state. Cap `max_parallel`; forbid writes outside the loop body's declared `files`.
- **Open:** parallel vs serial `verify` within a node. Default serial; revisit.
- **Open:** store a digest of the generating spec in the YAML to detect stale plans? Probably yes, out of scope for v1.
- **Open:** retry cap for `on_fail: retry`. Propose 2 then escalate.
