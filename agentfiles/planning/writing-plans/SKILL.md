---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
next: [subagent-driven-development]
---

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** This should be run in a dedicated worktree (created by brainstorming skill).

**Save plans to:** `docs/plans/YYYY-MM-DD-<feature-name>.md`
- (User preferences for plan location override this default)

## Scope Check

If the spec covers multiple independent subsystems, it should have been broken into sub-project specs during brainstorming. If it wasn't, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

## Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Remember
- Exact file paths always
- Complete code in plan (not "add validation")
- Exact commands with expected output
- Reference relevant skills with @ syntax
- DRY, YAGNI, TDD, frequent commits

## Machine Plan YAML Sidecar

Non-trivial plans ship as a **pair** — the prose markdown above, plus a sibling `docs/plans/YYYY-MM-DD-<feature-name>.yaml` that encodes the same task graph in a form `subagent-driven-development` can dispatch from directly. The prose is the authority for humans; the YAML is the authority for the executor.

**When to emit the YAML (complexity threshold from the YAML-plan design doc, §7):**

- ≥3 tasks, **or**
- any human gate (`pause` node), **or**
- any loop body (per-item fanout).

For **single-task bugfixes, simple one-file refactors, and plans short enough to hold on one screen (<3 tasks, no gates, no loops), prose alone is sufficient** — skip the YAML. Research/exploration plans whose output is a document (not code) also don't need a YAML.

**Schema** (full spec: `docs/plans/2026-04-18-plan-yaml-schema.md` §3):

```yaml
version: 1
plan:
  slug: <plan-slug>              # matches the markdown filename minus date/ext
  prose: docs/plans/<...>.md     # back-reference to the markdown authority
  goal: <one-sentence goal>

nodes:
  - id: <snake_case_unique>
    type: implement | review | verify | pause | loop
    depends_on: [<other_ids>]    # optional; empty = root
    description: <one-line intent>
    files:                       # optional mirror of the markdown table
      create: [...]
      modify: [...]
      test:   [...]
    verify:                      # optional shell commands; must exit 0
      - <cmd>
    on_fail: retry | escalate | pause    # default escalate
```

Type-specific fields: `review.reviewer` (`spec` | `code_quality`); `pause.prompt`; `loop.items` (list) or `loop.from` (path), `loop.body` (inline subgraph), `loop.max_parallel` (default 1, cap 10). `${item}` is the only templating primitive, scoped to loop bodies.

**Condensed worked example** — a 2-node slice showing shape (full example lives in the design doc §3):

```yaml
- id: cli_wiring
  type: implement
  depends_on: [spec_contract]
  description: Register `resume` on the session Typer app.
  verify:
    - uv run --directory tools/python af session resume --help

- id: human_gate_ux
  type: pause
  depends_on: [cli_wiring]
  prompt: Approve wording before docs?
```

### Dual-file consistency

- The markdown header carries a `**Machine plan:** <slug>.yaml` line beneath `**Goal:**`, pointing at the sidecar.
- The YAML's `plan.prose` points back at the markdown file.
- `af check` validates both sides — every `### Task N` in the prose has a matching `implement` node in the YAML, and the YAML's `prose:` resolves.

### Migration of existing prose-only plans

For in-flight plans written before the YAML schema existed, run:

```bash
uv run --project tools/python af plan-scaffold docs/plans/<YYYY-MM-DD-name>.md
```

This greps `### Task N:` headings and emits a YAML skeleton with one `implement` node per task, sequential `depends_on`. It's a starting point — you still fill in `verify:` commands, real dependency edges, and any human-gate / loop nodes by hand. Use `--force` to overwrite an existing sibling `.yaml`. Completed plans stay as-is; no auto-migration.

## Plan Review Loop

After writing the complete plan:

1. Dispatch a single plan-document-reviewer subagent (see plan-document-reviewer-prompt.md) with precisely crafted review context — never your session history. This keeps the reviewer focused on the plan, not your thought process.
   - Provide: path to the plan document, path to spec document
2. If ❌ Issues Found: fix the issues, re-dispatch reviewer for the whole plan
3. If ✅ Approved: proceed to execution handoff

**Review loop guidance:**
- Same agent that wrote the plan fixes it (preserves context)
- If loop exceeds 3 iterations, surface to human for guidance
- Reviewers are advisory — explain disagreements if you believe feedback is incorrect

## Execution Handoff

After saving the plan, offer execution choice:

**"Plan complete and saved to `docs/plans/<filename>.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?"**

**If Subagent-Driven chosen:**
- **REQUIRED SUB-SKILL:** Use subagent-driven-development
- Fresh subagent per task + two-stage review

**If Inline Execution chosen:**
- **REQUIRED SUB-SKILL:** Use executing-plans
- Batch execution with checkpoints for review
