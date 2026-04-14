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
