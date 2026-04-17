# Skill Tester — Design Spec

**Date:** 2026-04-14
**Status:** Approved

## Problem

Skills improve Claude's output quality, but there's no repeatable way to measure that improvement within the agentfiles project. The skill-creator plugin provides eval infrastructure but it's an external dependency. We need a project-native testing system that answers: "does this skill actually add value?"

## Solution

A `skill-tester` skill + `af test-skill` CLI command that runs skills against hard eval prompts with and without the skill, grades outputs against a rubric, and produces benchmark reports with scoring, timing, and token efficiency metrics.

## Components

### 1. `af test-skill <skill-name>` CLI Command

Lightweight scaffolding tool. Responsibilities:

- Validate `tests/<skill-name>/evals.json` exists (where `tests/` is at the project root: `/home/eastill/projects/agentfiles/tests/`)
- If missing, generate a template `evals.json` for the user to fill in
- Determine the next iteration number (scan for existing `iteration-N/` dirs)
- Create the workspace directory: `tests/<skill-name>/iteration-N/`
- Print: "Workspace ready at tests/<skill-name>/iteration-N/. Invoke the skill-tester skill to run evals."

Does NOT run evals, grade, or generate reports — that's the skill's job.

Note: This `tests/` directory is separate from `tools/python/tests/` which contains Python unit tests for the `af` CLI itself.

### 2. `tests/` Directory Structure

Located at project root: `/home/eastill/projects/agentfiles/tests/`

```
tests/
├── <skill-name>/
│   ├── evals.json                        # eval definitions + reference answers + rubric
│   ├── iteration-1/
│   │   ├── benchmark.json                # structured results
│   │   ├── <eval-name>/
│   │   │   ├── eval_metadata.json        # prompt + rubric snapshot
│   │   │   ├── with_skill/
│   │   │   │   ├── outputs/response.md   # full skill output
│   │   │   │   ├── grading.json          # rubric scores + evidence
│   │   │   │   └── timing.json           # duration_ms, total_tokens
│   │   │   └── without_skill/
│   │   │       ├── outputs/response.md
│   │   │       ├── grading.json
│   │   │       └── timing.json
│   │   └── <eval-name-2>/
│   │       └── ...
│   └── iteration-2/
│       └── ...
└── <another-skill>/
    └── evals.json
```

### 3. `evals.json` Schema

```json
{
  "version": 1,
  "skill_name": "dsa-expert",
  "skill_path": "agentfiles/coding/dsa/SKILL.md",
  "evals": [
    {
      "id": 0,
      "name": "k-most-frequent",
      "prompt": "Given a continuous stream of events, each identified by a string type, design a system that can efficiently report the top-k most frequent event types at any point in time. The stream can have millions of events and k can vary per query.",
      "reference_answer": "The optimal approach uses a HashMap for frequency counting combined with a bucket sort / frequency bucket array. Insert is O(1) amortized, top-k query is O(k + F) where F is the number of distinct frequencies. Key trade-offs: min-heap gives O(log k) per query but O(n log k) for top-k retrieval; quickselect gives O(n) average but O(n²) worst case; frequency buckets give O(k+F) query with O(1) insert. Edge cases include: k > distinct count, tie-breaking policy, frequency overflow, first-occurrence handling, and thread safety for concurrent streams."
    }
  ]
}
```

The `reference_answer` provides the known-correct answer so the grader can evaluate correctness and completeness against ground truth, not just structural quality.

### 4. Rubric

Every eval response (both with-skill and without-skill) is scored on 5 criteria using a 1-5 scale, plus 2 raw metrics. Each criterion is graded in a **separate LLM call** to prevent halo effects (one strong dimension inflating others).

#### Scored Criteria (1-5)

**Correctness** — Is the answer factually right and does it solve the problem?

| Score | Anchor |
|-------|--------|
| 1 | Fundamentally wrong approach or major factual errors |
| 2 | Partially correct but has significant errors that would cause bugs |
| 3 | Core approach is correct but has minor errors or misconceptions |
| 4 | Correct solution with only trivial issues |
| 5 | Fully correct, matches or exceeds the reference answer |

**Completeness** — Does it cover edge cases, constraints, trade-offs, and alternative approaches?

| Score | Anchor |
|-------|--------|
| 1 | Addresses only the happy path, ignores constraints |
| 2 | Mentions 1-2 considerations but misses major ones |
| 3 | Covers the main considerations, misses some edge cases |
| 4 | Thorough coverage with minor gaps |
| 5 | Comprehensive — constraints, trade-offs, edge cases, alternatives all addressed |

**Structure** — Is the response well-organized with clear sections and logical flow?

| Score | Anchor |
|-------|--------|
| 1 | Stream of consciousness, no organization |
| 2 | Some grouping but hard to navigate |
| 3 | Clear sections but flow could be improved |
| 4 | Well-organized with logical progression |
| 5 | Excellent structure — easy to scan, reference, and follow |

**Clarity** — Is the explanation clear, concise, and free of unnecessary verbosity?

| Score | Anchor |
|-------|--------|
| 1 | Confusing, contradictory, or impenetrable |
| 2 | Understandable but verbose or uses jargon without explanation |
| 3 | Clear for the most part, some sections could be tighter |
| 4 | Clear and concise throughout |
| 5 | Exceptionally clear — complex ideas explained simply |

**Actionability** — Can someone take this output and implement/use it directly?

| Score | Anchor |
|-------|--------|
| 1 | Purely theoretical, no implementation guidance |
| 2 | Some hints but significant work needed to implement |
| 3 | Provides a starting point but missing key details |
| 4 | Implementable with minor research needed |
| 5 | Ready to implement — pseudocode, data structures, and language-specific guidance provided |

#### Raw Metrics (measured, not scored)

- **Tokens**: Total tokens consumed by the agent
- **Time**: Wall-clock seconds for the agent to complete

#### Composite Score

Each eval produces: a total rubric score (sum of 5 criteria, max 25), plus raw token and time metrics. The benchmark aggregates these across all evals to produce averages and deltas between with-skill and without-skill.

**Tokens per rubric point** = total_tokens / total_rubric_score — measures how efficiently the skill converts tokens into quality. Lower is better.

### 5. Eval Sourcing — Hard Questions

Each skill should have **4 eval questions**. When creating evals, the skill-tester instructs Claude to **search online for difficult interview and benchmarking questions** rather than inventing generic test cases. Sources include:

- LeetCode Hard / competitive programming problems
- System design interview questions (e.g., "design a rate limiter," "design a distributed cache")
- Known algorithm benchmarks (CLRS problems, TopCoder/Codeforces editorial problems)
- Domain-specific challenges relevant to the skill being tested

The goal is to stress-test skills against problems where structured thinking matters most — easy problems score well with or without the skill and don't discriminate.

After finding questions, Claude researches and writes the `reference_answer` for each so the grader has ground truth to evaluate against.

### 6. `docs/testing/<skill-name>.md` Report

Overwritten each run with the latest iteration's results. Contains:

```markdown
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

| Eval                | Config        | Corr | Comp | Struct | Clar | Action | Total | Tokens | Time (s) |
|---------------------|---------------|------|------|--------|------|--------|-------|--------|----------|
| k-most-frequent     | with_skill    | 5    | 5    | 5      | 4    | 5      | 24    | 16,254 | 103.2    |
| k-most-frequent     | without_skill | 4    | 3    | 3      | 4    | 2      | 16    | 12,235 | 64.9     |
| autocomplete        | with_skill    | 5    | 4    | 5      | 4    | 4      | 22    | 16,007 | 98.9     |
| ...                 | ...           | ...  | ...  | ...    | ...  | ...    | ...   | ...    | ...      |

## Analysis

- **Biggest skill impact:** Actionability (+2.0) and Structure (+1.8) — the skill forces organized, implementable output
- **Smallest impact:** Correctness (+0.6) — the model is already good at getting the right answer
- **Token efficiency:** Skill uses 33% more tokens but scores 43% higher — net tokens-per-rubric-point is better with the skill
- **Verdict:** Skill adds significant value. Recommended for use.
```

### 7. `skill-tester` SKILL.md

Lives at `agentfiles/coding/quality/skill-tester/SKILL.md`.

**Trigger:** User wants to test/evaluate a skill, or runs `af test-skill`.

**Process the skill instructs Claude to follow:**

1. **Setup** — Read `tests/<skill-name>/evals.json`. If it doesn't exist, guide the user to run `af test-skill <skill-name>` first. If the template is empty, search online for 4 hard questions relevant to the skill's domain, research correct answers, and populate the evals.json with prompts and reference answers.

2. **Spawn parallel agents** — For each eval, spawn two agents in parallel:
   - **With-skill agent:** Prompt includes the full content of the skill's SKILL.md (read and injected into the agent prompt), plus the eval question. The agent is told to follow the skill's instructions to answer the question. Save output to `with_skill/outputs/response.md`. Record timing.
   - **Without-skill agent:** Same eval question, no skill content in prompt. Just "Answer this question:" + the eval prompt. Save output to `without_skill/outputs/response.md`. Record timing.
   - All eval pairs run in parallel (up to 8 agents for 4 evals).
   - The "without-skill" condition is enforced by simply not including the skill content in the agent's prompt — the agent has no access to the SKILL.md.

3. **Grade outputs** — For each response, grade each of the 5 rubric criteria in a **separate agent call** (to prevent halo effects). Each grading agent receives:
   - The eval prompt
   - The reference answer
   - The response being graded
   - The rubric for that single criterion (with behavioral anchors)
   - Instruction to output: score (1-5), evidence (1-2 sentences justifying the score)
   - This means 10 grading calls per eval (5 criteria × 2 configurations), 40 total for 4 evals. These can all run in parallel.
   - Write `grading.json` per response.

4. **Aggregate** — Compute per-criterion averages across evals, total rubric scores, timing averages and stddev, token averages and stddev, tokens-per-rubric-point ratio. Write `benchmark.json`.

5. **Write report** — Generate `docs/testing/<skill-name>.md` with the full report.

### 8. JSON Schemas for Output Files

**timing.json:**
```json
{
  "total_tokens": 16007,
  "duration_ms": 98900,
  "total_duration_seconds": 98.9
}
```

**grading.json:**
```json
{
  "eval_id": 0,
  "run_id": "k-most-frequent-with_skill",
  "scores": [
    {
      "criterion": "correctness",
      "score": 5,
      "evidence": "Solution correctly identifies frequency bucket approach as optimal, with accurate O(1) insert and O(k+F) query analysis"
    },
    {
      "criterion": "completeness",
      "score": 5,
      "evidence": "Covers 9 edge cases including tie-breaking, overflow, thread safety, and sparse gaps; compares 3 approaches across 8 criteria"
    },
    {
      "criterion": "structure",
      "score": 5,
      "evidence": "Clear numbered steps matching the skill's process, with distinct constraint summary, trade-off table, pseudocode, and edge case sections"
    },
    {
      "criterion": "clarity",
      "score": 4,
      "evidence": "Generally clear and well-explained, some sections slightly verbose in the complexity proof"
    },
    {
      "criterion": "actionability",
      "score": 5,
      "evidence": "Clean pseudocode for both data structure and query, with Python/Rust/TypeScript-specific library recommendations"
    }
  ],
  "total_score": 24,
  "max_score": 25
}
```

**benchmark.json:**
```json
{
  "metadata": {
    "skill_name": "dsa-expert",
    "skill_path": "agentfiles/coding/dsa/SKILL.md",
    "timestamp": "2026-04-14T00:10:00Z",
    "evals_run": ["k-most-frequent", "autocomplete", "dag-parallel-execution", "lru-cache"],
    "num_evals": 4
  },
  "runs": [
    {
      "configuration": "with_skill",
      "avg_scores": {
        "correctness": 4.8,
        "completeness": 4.5,
        "structure": 4.8,
        "clarity": 4.3,
        "actionability": 4.5,
        "total": 22.9
      },
      "avg_time_seconds": 105.4,
      "time_stddev": 6.5,
      "avg_tokens": 16443,
      "tokens_stddev": 447,
      "tokens_per_rubric_point": 718,
      "per_eval": [
        {
          "eval_name": "k-most-frequent",
          "scores": {"correctness": 5, "completeness": 5, "structure": 5, "clarity": 4, "actionability": 5, "total": 24},
          "time_seconds": 103.2,
          "tokens": 16254
        }
      ]
    },
    {
      "configuration": "without_skill",
      "avg_scores": {
        "correctness": 4.2,
        "completeness": 2.8,
        "structure": 3.0,
        "clarity": 3.5,
        "actionability": 2.5,
        "total": 16.0
      },
      "avg_time_seconds": 62.4,
      "time_stddev": 2.1,
      "avg_tokens": 12349,
      "tokens_stddev": 231,
      "tokens_per_rubric_point": 772,
      "per_eval": []
    }
  ],
  "delta": {
    "correctness": "+0.6",
    "completeness": "+1.7",
    "structure": "+1.8",
    "clarity": "+0.8",
    "actionability": "+2.0",
    "total": "+6.9",
    "time_seconds": "+43.0",
    "tokens": "+4094",
    "tokens_per_rubric_point": "-54"
  }
}
```

**eval_metadata.json:**
```json
{
  "eval_id": 0,
  "eval_name": "k-most-frequent",
  "prompt": "Given a continuous stream of events...",
  "reference_answer": "The optimal approach uses a HashMap..."
}
```

## What's NOT in Scope

- No browser-based viewer (the markdown report is sufficient)
- No API key management in the CLI
- No automatic assertion suggestion
- No cross-skill comparison reports
- No CI integration (manual runs only)
- No repeated runs of the same eval (stddev is computed across the 4 different evals, not repeated trials — one run per eval per configuration)

## Implementation Order

1. Add `test-skill` subcommand to `af` CLI (`tools/python/`)
2. Create `skill-tester` SKILL.md
3. Create `tests/` directory at project root with template structure
4. Create `docs/testing/` directory
5. Test the skill by running it against the DSA expert skill
