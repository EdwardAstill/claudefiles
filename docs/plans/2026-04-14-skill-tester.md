# Skill Tester Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a skill-testing system with `af test-skill` CLI scaffolding and a `skill-tester` SKILL.md that evaluates skills against hard questions using rubric-based grading.

**Architecture:** `af test-skill <name>` creates workspace directories and template evals.json. The `skill-tester` skill guides Claude through spawning with/without-skill agents, grading outputs on 5 rubric criteria via isolated grading calls, aggregating results into benchmark.json, and writing a human-readable report to `docs/testing/`.

**Tech Stack:** Python (Typer CLI), Markdown (SKILL.md, reports)

**Spec:** `docs/specs/2026-04-14-skill-tester-design.md`

---

## File Structure

| File | Responsibility |
|------|----------------|
| `tools/python/src/af/test_skill.py` | CLI subcommand — scaffolding, template generation, workspace creation |
| `tools/python/src/af/main.py` | Register `test-skill` subcommand (one line addition) |
| `tools/python/tests/test_test_skill.py` | Tests for the CLI subcommand |
| `agentfiles/coding/quality/skill-tester/SKILL.md` | Skill that guides Claude through eval execution, grading, aggregation, and reporting |
| `tests/` (project root) | Top-level directory for all skill eval data |
| `docs/testing/` | Directory for generated test reports |

---

### Task 1: `af test-skill` CLI — Test + Implementation

**Files:**
- Create: `tools/python/src/af/test_skill.py`
- Modify: `tools/python/src/af/main.py:6-27` (add to `_SUBCOMMANDS`)
- Create: `tools/python/tests/test_test_skill.py`

- [ ] **Step 1: Write failing tests for `af test-skill`**

Create `tools/python/tests/test_test_skill.py`:

```python
import json
from typer.testing import CliRunner
from af.main import app

runner = CliRunner()


def test_no_evals_creates_template(git_repo, monkeypatch):
    """When no evals.json exists, create a template."""
    monkeypatch.chdir(git_repo)
    (git_repo / "tests").mkdir()
    result = runner.invoke(app, ["test-skill", "dsa-expert"])
    assert result.exit_code == 0
    template = git_repo / "tests" / "dsa-expert" / "evals.json"
    assert template.exists()
    data = json.loads(template.read_text())
    assert data["skill_name"] == "dsa-expert"
    assert data["version"] == 1
    assert len(data["evals"]) == 0
    assert "template" in result.output.lower() or "created" in result.output.lower()


def test_existing_evals_creates_workspace(git_repo, monkeypatch):
    """When evals.json exists, create iteration-N workspace."""
    monkeypatch.chdir(git_repo)
    skill_dir = git_repo / "tests" / "dsa-expert"
    skill_dir.mkdir(parents=True)
    evals = {
        "version": 1,
        "skill_name": "dsa-expert",
        "skill_path": "agentfiles/coding/dsa/SKILL.md",
        "evals": [
            {"id": 0, "name": "test-eval", "prompt": "test", "reference_answer": "answer"}
        ]
    }
    (skill_dir / "evals.json").write_text(json.dumps(evals))
    result = runner.invoke(app, ["test-skill", "dsa-expert"])
    assert result.exit_code == 0
    assert (skill_dir / "iteration-1").is_dir()
    assert "iteration-1" in result.output


def test_increments_iteration(git_repo, monkeypatch):
    """When iteration-1 exists, create iteration-2."""
    monkeypatch.chdir(git_repo)
    skill_dir = git_repo / "tests" / "dsa-expert"
    skill_dir.mkdir(parents=True)
    (skill_dir / "iteration-1").mkdir()
    evals = {
        "version": 1,
        "skill_name": "dsa-expert",
        "skill_path": "agentfiles/coding/dsa/SKILL.md",
        "evals": [{"id": 0, "name": "test-eval", "prompt": "test", "reference_answer": "answer"}]
    }
    (skill_dir / "evals.json").write_text(json.dumps(evals))
    result = runner.invoke(app, ["test-skill", "dsa-expert"])
    assert result.exit_code == 0
    assert (skill_dir / "iteration-2").is_dir()
    assert "iteration-2" in result.output


def test_empty_evals_warns(git_repo, monkeypatch):
    """When evals.json exists but has no evals, warn the user."""
    monkeypatch.chdir(git_repo)
    skill_dir = git_repo / "tests" / "dsa-expert"
    skill_dir.mkdir(parents=True)
    evals = {
        "version": 1,
        "skill_name": "dsa-expert",
        "skill_path": "agentfiles/coding/dsa/SKILL.md",
        "evals": []
    }
    (skill_dir / "evals.json").write_text(json.dumps(evals))
    result = runner.invoke(app, ["test-skill", "dsa-expert"])
    assert result.exit_code == 0
    assert "no evals" in result.output.lower() or "empty" in result.output.lower()


def test_no_tests_dir_creates_it(git_repo, monkeypatch):
    """When tests/ doesn't exist at all, create it."""
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["test-skill", "my-skill"])
    assert result.exit_code == 0
    assert (git_repo / "tests" / "my-skill" / "evals.json").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/eastill/projects/agentfiles && python -m pytest tools/python/tests/test_test_skill.py -v`
Expected: FAIL — `af.test_skill` module not found

- [ ] **Step 3: Implement `af test-skill`**

Create `tools/python/src/af/test_skill.py`:

```python
import json
from pathlib import Path

import typer

from af.lib import git_root

app = typer.Typer(invoke_without_command=True)

_TEMPLATE = {
    "version": 1,
    "skill_name": "",
    "skill_path": "",
    "evals": []
}


def _next_iteration(skill_dir: Path) -> int:
    n = 1
    while (skill_dir / f"iteration-{n}").exists():
        n += 1
    return n


@app.callback(invoke_without_command=True)
def main(
    skill_name: str = typer.Argument(..., help="Name of the skill to test"),
):
    """Scaffold a skill test workspace."""
    root = git_root()
    tests_dir = root / "tests"
    skill_dir = tests_dir / skill_name
    evals_path = skill_dir / "evals.json"

    # No evals.json — create template
    if not evals_path.exists():
        skill_dir.mkdir(parents=True, exist_ok=True)
        template = {**_TEMPLATE, "skill_name": skill_name}
        evals_path.write_text(json.dumps(template, indent=2) + "\n")
        typer.echo(f"Created template at {evals_path.relative_to(root)}")
        typer.echo("Fill in skill_path, evals (with prompt + reference_answer), then run again.")
        return

    # Load and validate
    data = json.loads(evals_path.read_text())
    if not data.get("evals"):
        typer.echo(f"No evals defined in {evals_path.relative_to(root)}. Add evals and run again.")
        return

    # Create workspace
    n = _next_iteration(skill_dir)
    workspace = skill_dir / f"iteration-{n}"
    workspace.mkdir(parents=True)
    typer.echo(f"Workspace ready at {workspace.relative_to(root)}/")
    typer.echo("Invoke the skill-tester skill to run evals.")
```

- [ ] **Step 4: Register in main.py**

Add to `_SUBCOMMANDS` in `tools/python/src/af/main.py`:

```python
("test-skill", "test_skill"),
```

Add it after the last entry (before the closing `]`).

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/eastill/projects/agentfiles && python -m pytest tools/python/tests/test_test_skill.py -v`
Expected: All 5 tests PASS

- [ ] **Step 6: Commit**

```bash
git add tools/python/src/af/test_skill.py tools/python/src/af/main.py tools/python/tests/test_test_skill.py
git commit -m "feat: add af test-skill CLI command for skill eval scaffolding"
```

---

### Task 2: Create `skill-tester` SKILL.md

**Files:**
- Create: `agentfiles/coding/quality/skill-tester/SKILL.md`

- [ ] **Step 1: Create the skill directory**

```bash
mkdir -p agentfiles/coding/quality/skill-tester
```

- [ ] **Step 2: Write SKILL.md**

Create `agentfiles/coding/quality/skill-tester/SKILL.md`:

```markdown
---
name: skill-tester
description: >
  Tests and evaluates agentfiles skills by running them against hard benchmark
  questions and grading outputs on a rubric. Use when you want to measure
  whether a skill adds value, after running `af test-skill <name>`, or when
  asked to test, evaluate, benchmark, or grade a skill. Triggers on: "test
  this skill", "does this skill help", "evaluate the skill", "benchmark",
  "run evals", "grade the skill", or any request to measure skill quality.
---

# Skill Tester

Evaluates whether a skill adds measurable value by running it against hard
questions with and without the skill, then grading outputs on a rubric.

## When to Use

- User runs `af test-skill <name>` and asks you to run evals
- User asks "does this skill help?" or "test this skill"
- After creating or modifying a skill, to verify it adds value

## When NOT to Use

- Testing code (use TDD skill)
- Reviewing code quality (use code-review skill)

## Process

### Step 1: Load Evals

Read `tests/<skill-name>/evals.json`. If it doesn't exist:

1. Tell the user to run `af test-skill <skill-name>` to create the template
2. Once the template exists, **search online** for 4 hard questions relevant to
   the skill's domain:
   - LeetCode Hard / competitive programming for algorithm skills
   - System design interview questions for architecture skills
   - Domain-specific benchmarks (e.g., security CTFs for security skills)
   - Known hard problems from textbooks or editorial sites
3. For each question, research the correct answer thoroughly
4. Populate `evals.json` with the 4 prompts and reference answers

If evals.json already has evals, proceed to Step 2.

### Step 2: Determine Workspace

Find the latest `tests/<skill-name>/iteration-N/` directory. If none exists,
tell the user to run `af test-skill <skill-name>` again.

### Step 3: Run Evals

For each eval in evals.json, spawn **two agents in parallel**:

**With-skill agent prompt:**
```
You are answering a technical question. Follow the skill instructions below
carefully when formulating your response.

## Skill Instructions

<insert full content of the skill's SKILL.md here, read via Read tool>

## Question

<insert eval prompt>
```

**Without-skill agent prompt:**
```
Answer the following technical question thoroughly.

## Question

<insert eval prompt>
```

- Spawn all eval pairs in parallel (up to 8 agents for 4 evals)
- Save each agent's output to `<eval-name>/with_skill/outputs/response.md`
  or `<eval-name>/without_skill/outputs/response.md`
- Record timing: measure wall-clock time from agent dispatch to completion,
  and note total tokens from the agent result metadata. Write `timing.json`:
  ```json
  {
    "total_tokens": 16007,
    "duration_ms": 98900,
    "total_duration_seconds": 98.9
  }
  ```
- Write `eval_metadata.json` for each eval:
  ```json
  {
    "eval_id": 0,
    "eval_name": "k-most-frequent",
    "prompt": "Given a continuous stream...",
    "reference_answer": "The optimal approach uses..."
  }
  ```

### Step 4: Grade Outputs

For each response, grade each criterion in a **separate agent call** to prevent
halo effects. That's 5 criteria × 2 configurations × N evals = 10N grading
calls. Run them all in parallel.

**Grading agent prompt (one per criterion):**
```
You are grading a technical response on a single criterion.

## The Question
<eval prompt>

## Reference Answer (ground truth)
<reference_answer from evals.json>

## Response Being Graded
<the agent's response.md>

## Criterion: <criterion name>
<criterion description and behavioral anchors from the rubric below>

Score this response 1-5 on this criterion ONLY. Output JSON:
{"score": <1-5>, "evidence": "<1-2 sentences justifying the score>"}
```

#### Rubric

**Correctness** — Is the answer factually right and does it solve the problem?
- 1: Fundamentally wrong approach or major factual errors
- 2: Partially correct but has significant errors that would cause bugs
- 3: Core approach is correct but has minor errors or misconceptions
- 4: Correct solution with only trivial issues
- 5: Fully correct, matches or exceeds the reference answer

**Completeness** — Does it cover edge cases, constraints, trade-offs?
- 1: Addresses only the happy path, ignores constraints
- 2: Mentions 1-2 considerations but misses major ones
- 3: Covers the main considerations, misses some edge cases
- 4: Thorough coverage with minor gaps
- 5: Comprehensive — constraints, trade-offs, edge cases, alternatives all addressed

**Structure** — Is the response well-organized with clear sections and logical flow?
- 1: Stream of consciousness, no organization
- 2: Some grouping but hard to navigate
- 3: Clear sections but flow could be improved
- 4: Well-organized with logical progression
- 5: Excellent structure — easy to scan, reference, and follow

**Clarity** — Is the explanation clear, concise, and free of unnecessary verbosity?
- 1: Confusing, contradictory, or impenetrable
- 2: Understandable but verbose or uses jargon without explanation
- 3: Clear for the most part, some sections could be tighter
- 4: Clear and concise throughout
- 5: Exceptionally clear — complex ideas explained simply

**Actionability** — Can someone take this output and implement/use it directly?
- 1: Purely theoretical, no implementation guidance
- 2: Some hints but significant work needed to implement
- 3: Provides a starting point but missing key details
- 4: Implementable with minor research needed
- 5: Ready to implement — pseudocode, data structures, and language-specific guidance provided

Write `grading.json` for each response:
```json
{
  "eval_id": 0,
  "run_id": "k-most-frequent-with_skill",
  "scores": [
    {"criterion": "correctness", "score": 5, "evidence": "..."},
    {"criterion": "completeness", "score": 5, "evidence": "..."},
    {"criterion": "structure", "score": 5, "evidence": "..."},
    {"criterion": "clarity", "score": 4, "evidence": "..."},
    {"criterion": "actionability", "score": 5, "evidence": "..."}
  ],
  "total_score": 24,
  "max_score": 25
}
```

### Step 5: Aggregate

Read all grading.json and timing.json files. Compute:

- Per-criterion averages for with_skill and without_skill
- Total rubric score averages
- Timing averages and standard deviation (across evals)
- Token averages and standard deviation (across evals)
- **Tokens per rubric point** = avg_tokens / avg_total_score (lower is better)
- Deltas between configurations for all metrics

Write `benchmark.json`:
```json
{
  "metadata": {
    "skill_name": "dsa-expert",
    "skill_path": "agentfiles/coding/dsa/SKILL.md",
    "timestamp": "2026-04-14T00:10:00Z",
    "evals_run": ["k-most-frequent", "autocomplete", "dag-parallel", "lru-cache"],
    "num_evals": 4
  },
  "runs": [
    {
      "configuration": "with_skill",
      "avg_scores": {
        "correctness": 4.8, "completeness": 4.5, "structure": 4.8,
        "clarity": 4.3, "actionability": 4.5, "total": 22.9
      },
      "avg_time_seconds": 105.4,
      "time_stddev": 6.5,
      "avg_tokens": 16443,
      "tokens_stddev": 447,
      "tokens_per_rubric_point": 718
    },
    {
      "configuration": "without_skill",
      "avg_scores": {
        "correctness": 4.2, "completeness": 2.8, "structure": 3.0,
        "clarity": 3.5, "actionability": 2.5, "total": 16.0
      },
      "avg_time_seconds": 62.4,
      "time_stddev": 2.1,
      "avg_tokens": 12349,
      "tokens_stddev": 231,
      "tokens_per_rubric_point": 772,
      "per_eval": [
        {
          "eval_name": "k-most-frequent",
          "scores": {"correctness": 4, "completeness": 3, "structure": 3, "clarity": 4, "actionability": 2, "total": 16},
          "time_seconds": 64.9,
          "tokens": 12235
        }
      ]
    }
  ],
  "delta": {
    "correctness": "+0.6", "completeness": "+1.7", "structure": "+1.8",
    "clarity": "+0.8", "actionability": "+2.0", "total": "+6.9",
    "time_seconds": "+43.0", "tokens": "+4094",
    "tokens_per_rubric_point": "-54"
  }
}
```

### Step 6: Write Report

Generate `docs/testing/<skill-name>.md` (overwrite if exists). Use this template:

````
# <Skill Name> — Test Report

**Date:** YYYY-MM-DD
**Iteration:** N
**Evals run:** 4

## Rubric Scores (1-5 scale)

| Criterion      | With Skill (avg) | Without Skill (avg) | Delta  |
|----------------|-------------------|---------------------|--------|
| Correctness    | 4.8               | 4.2                 | +0.6   |
| Completeness   | 4.5               | 2.8                 | +1.7   |
| Structure      | 4.8               | 3.0                 | +1.8   |
| Clarity        | 4.3               | 3.5                 | +0.8   |
| Actionability  | 4.5               | 2.5                 | +2.0   |
| **Total (/25)**| **22.9**          | **16.0**            | **+6.9**|

## Timing

| Configuration   | Avg Time (s) | Std Dev |
|-----------------|-------------|---------|
| With skill      | 105.4       | ±6.5    |
| Without skill   | 62.4        | ±2.1    |
| **Delta**       | **+43.0**   |         |

## Token Efficiency

| Configuration   | Avg Tokens | Std Dev | Tokens per Rubric Point |
|-----------------|-----------|---------|-------------------------|
| With skill      | 16,443    | ±447    | 718                     |
| Without skill   | 12,349    | ±231    | 772                     |
| **Delta**       | **+4,094**|         | **-54 (better)**        |

## Per-Eval Breakdown

| Eval            | Config        | Corr | Comp | Struct | Clar | Action | Total | Tokens | Time (s) |
|-----------------|---------------|------|------|--------|------|--------|-------|--------|----------|
| k-most-frequent | with_skill    | 5    | 5    | 5      | 4    | 5      | 24    | 16,254 | 103.2    |
| k-most-frequent | without_skill | 4    | 3    | 3      | 4    | 2      | 16    | 12,235 | 64.9     |
| ...             | ...           | ...  | ...  | ...    | ...  | ...    | ...   | ...    | ...      |

## Analysis

- **Biggest skill impact:** <criteria with largest delta>
- **Smallest impact:** <criteria with smallest delta>
- **Token efficiency:** <comparison of tokens-per-rubric-point>
- **Verdict:** <does this skill add value? recommended for use?>
````

Replace example values with actual computed data from benchmark.json.

## Anti-Patterns

- **Don't grade all criteria in one call** — this causes halo effects where
  one strong dimension inflates scores on others
- **Don't use easy questions** — they won't discriminate between with/without
  skill. Search for genuinely hard problems.
- **Don't skip the reference answer** — without ground truth, the grader
  can't assess correctness properly
- **Don't invent questions from scratch** — search online for established
  hard problems. Real interview/benchmark questions are better calibrated.
```

- [ ] **Step 3: Commit**

```bash
git add agentfiles/coding/quality/skill-tester/SKILL.md
git commit -m "feat: add skill-tester skill for rubric-based skill evaluation"
```

---

### Task 3: Create Project Directories and Symlink

**Files:**
- Create: `tests/` directory at project root
- Create: `docs/testing/` directory
- Create: `skills/skill-tester` symlink (if the project uses symlinks for skill installation)

- [ ] **Step 1: Create the directories**

```bash
mkdir -p tests
mkdir -p docs/testing
```

- [ ] **Step 2: Add skill symlink**

Check if `skills/` directory uses symlinks (it does based on project structure):

```bash
ln -s ../agentfiles/coding/quality/skill-tester skills/skill-tester
```

- [ ] **Step 3: Add .gitkeep files so git tracks the empty directories**

```bash
touch tests/.gitkeep
touch docs/testing/.gitkeep
```

- [ ] **Step 4: Add skill-tester to manifest.toml**

Add this entry to `manifest.toml`:

```toml
[skills.skill-tester]
tools = ["Read", "Write", "Agent", "Bash", "Glob", "Grep", "WebSearch"]
category = "coding/quality"
```

The skill needs: `Read` (load evals.json, skill files), `Write` (save outputs, grading, reports), `Agent` (spawn eval and grading agents), `Bash` (run af commands), `Glob`/`Grep` (find workspace files), `WebSearch` (find hard questions).

- [ ] **Step 5: Commit**

```bash
git add tests/.gitkeep docs/testing/.gitkeep skills/skill-tester manifest.toml
git commit -m "feat: add tests/ and docs/testing/ directories for skill evaluation"
```

---

### Task 4: Integration Test — Run Against DSA Expert Skill

This task validates the entire system end-to-end.

- [ ] **Step 1: Run `af test-skill dsa-expert`**

```bash
af test-skill dsa-expert
```

Expected: Creates `tests/dsa-expert/evals.json` template.

- [ ] **Step 2: Populate evals.json**

Invoke the skill-tester skill. It should:
- Search online for 4 hard DSA questions
- Research reference answers
- Write them into `tests/dsa-expert/evals.json`

- [ ] **Step 3: Run `af test-skill dsa-expert` again**

```bash
af test-skill dsa-expert
```

Expected: Creates `tests/dsa-expert/iteration-1/` workspace.

- [ ] **Step 4: Run the skill-tester skill**

The skill should:
- Spawn 8 agents (4 with-skill + 4 without-skill)
- Spawn 40 grading agents (5 criteria × 2 configs × 4 evals)
- Write all grading.json, timing.json, benchmark.json
- Generate `docs/testing/dsa-expert.md`

- [ ] **Step 5: Verify the report**

Read `docs/testing/dsa-expert.md` and confirm:
- Rubric scores table present with with/without comparison
- Timing table present with averages and stddev
- Token efficiency table present with tokens-per-rubric-point
- Per-eval breakdown table present
- Analysis section with verdict

- [ ] **Step 6: Commit results**

```bash
git add tests/dsa-expert/ docs/testing/dsa-expert.md
git commit -m "test: run skill-tester against dsa-expert skill — first eval"
```
