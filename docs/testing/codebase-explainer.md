# codebase-explainer — Skill Benchmark Report

**Skill:** `agentfiles/research/codebase-explainer/SKILL.md`
**Iteration:** 1
**Workspace:** `tests/codebase-explainer/iteration-1/`
**Target repo:** the agentfiles repo itself (`/home/eastill/projects/agentfiles`) — real code with ground-truth reference answers authored from first-hand inspection
**Evals:** 4 hard benchmark questions covering the skill's three pillars: architecture mapping, execution-path tracing, abstraction surfacing — plus a cross-cutting "where would I change X" question
**Method:** `skill-tester` pipeline — with-skill vs without-skill responses, 5-criterion rubric (Correctness, Completeness, Structure, Clarity, Actionability), graded against reference answers derived from reading the actual code.

## Rubric Scores

| Criterion       | With skill | Without skill | Delta  |
|-----------------|:----------:|:-------------:|:------:|
| Correctness     |    5.00    |     4.25      | +0.75  |
| Completeness    |    5.00    |     3.00      | +2.00  |
| Structure       |    5.00    |     3.75      | +1.25  |
| Clarity         |    4.00    |     5.00      | -1.00  |
| Actionability   |    5.00    |     3.25      | +1.75  |
| **Total / 25**  |  **24.00** |   **19.25**   | **+4.75** |

## Token / Verbosity

Estimated from word count (words × 1.35). Prompt side not counted.

| Metric                         | With skill | Without skill | Delta   |
|--------------------------------|:----------:|:-------------:|:-------:|
| Mean tokens / response         |   1,599    |      385      | +1,214  |
| Tokens per rubric point        |    66.6    |     20.0      | +46.6   |

With-skill responses are about 4.2× longer. That cost buys the +4.75 rubric delta; in terms of marginal tokens per marginal rubric point the ratio is 1,214 / 4.75 ≈ 256 tokens per extra rubric point — consistent with the dsa-expert iteration-1 result (239 tokens/point) and suggesting the skill's "structured process for structured output" tradeoff has a similar shape across domains.

## Per-Eval Breakdown

| Eval                                     | With | Without | Delta | Notes |
|------------------------------------------|:----:|:-------:|:-----:|-------|
| architecture-layers-af-cli               |  24  |   21    | +3    | Baseline already strong on correctness and clarity (5/5 each). Skill wins on completeness (pitfalls like the dual _SUBCOMMANDS + manifest.toml registry, silent ModuleNotFoundError guard) and actionability (structured 'when to stop' checklist). |
| trace-plan-exec-path                     |  24  |   18    | +6    | Largest delta. With-skill enumerates all 7 validator invariants letter-by-letter, 5 fork points, external-call categorization, and flags the phase-2A/2C architectural disclaimer up-front. Without-skill compresses these into short paragraphs. |
| abstractions-hooks-system                |  24  |   19    | +5    | With-skill uses consistent sub-structure per abstraction (defines / shape / for / consumers), surfaces the `hook_types.py` vs `types.py` stdlib-shadowing pitfall, and notes the escalation rule's hardcoded string-literal fragility. Without-skill names the abstractions but lacks the gotchas. |
| where-to-change-skill-loading            |  24  |   19    | +5    | With-skill opens with a critical reframe ("agentfiles has no runtime skill-loader — Claude Code reads SKILL.md directly, installer is the touch point"), then gives 10 ordered change steps with Why/Change-type per entry, plus 4 security options with a pragmatic default and 5 named test cases. Without-skill lists the right files but doesn't scaffold the reasoning. |

## Analysis

### What the skill buys

- **Completeness (+2.00).** The 5-step process forces explicit layer tables, fork-point enumeration, and pitfall sections. Without the skill, the baseline answer names the right files but doesn't systematically cover edge cases, gotchas, or non-obvious constraints. This is the largest single contributor.
- **Actionability (+1.75).** The Step-5 "when to stop" section consistently produces worked "where would I add X / what breaks if I change Y / what does Z depend on" examples. The without-skill responses name files but leave the reader to synthesize the actionable rules themselves.
- **Structure (+1.25).** The 5-step skeleton (Orient → Layers → Execution Path → Abstractions → Mental Model + Stop) is easier to verify against and to skim. Without-skill responses are flat paragraphs; with-skill uses tables, numbered steps, and explicit headers per step.
- **Correctness (+0.75).** The smallest gain, and that's the right signal — the baseline agent is genuinely competent at reading code. The skill's gain here comes from catching subtleties (e.g., that both validate and toposort do cycle detection but disagree on surface; that hook_types.py must NOT be renamed to types.py because of stdlib shadowing) that a short answer can miss.

### What the skill costs

- **Clarity (-1.00).** With-skill responses are 4.2× longer. Information density is fine per paragraph, but a reader wanting a quick sketch finds the without-skill version faster to scan. The clarity score anchors on "no unnecessary verbosity" — with-skill is never padded, but it is long by design.
- **Token budget.** Roughly 1,214 extra tokens per response. For codebase-onboarding tasks where the output is consumed once and acted on for days or weeks, this is a favorable trade. For quick "where is function X defined" questions, the baseline is enough.

### Consistency across the 3 skill pillars

The eval design targeted the skill's stated three pillars explicitly:

- **Architecture mapping** (`architecture-layers-af-cli`) — +3
- **Execution-path tracing** (`trace-plan-exec-path`) — +6
- **Abstraction surfacing** (`abstractions-hooks-system`) — +5
- **Cross-cutting change scoping** (`where-to-change-skill-loading`) — +5

All four deltas positive; the spread (+3 to +6) suggests the skill's gain is real but scales with question complexity — the simpler architecture-layers question had the narrowest gap because the baseline answer was already well-structured for that type of question. The execution-tracing question, which requires enumerating invariants and forks, shows the largest gain because those are the parts the skill's process explicitly promotes.

### Comparison to dsa-expert iteration-1

Almost identical aggregate (+4.75/25 vs +4.75/25) and nearly identical token-efficiency shape (255 vs 239 marginal tokens per rubric point). Both skills trade verbosity for structure, catch subtleties the baseline misses, and lose only on clarity because of length. This is useful calibration: skills that encode a multi-step process produce a consistent ~4–5 point rubric gain at ~3–4× verbosity cost. The skills are effective for roughly the same reason and at roughly the same price.

### Where the skill could tighten

1. **Step 2 (Map the Architecture Layers) sometimes produces a long inline file list** when the subcommand layer has 30+ modules. The eval 0 answer's layer-2 enumeration reads slower than the rest — a note in the skill like "for layers with >10 members, list 5 representative files and mention the rest as 'etc., ~N total'" would help.
2. **The "When to Stop" checklist (end of Step 5) is the highest-leverage anti-verbosity mechanism in the skill.** It explicitly bounds the output by asking "can you answer these 3 questions." Could be promoted earlier in the skill — e.g., "frame your orient step with the stop-criteria you'd want to satisfy" — to bias the whole response toward what the reader will act on.
3. **Step 3 (trace a key execution path) currently assumes a single path.** In the eval 1 answer, the execution path has 6 subcommand leaves and had to be composed as a branching list. A note like "if there are multiple equally-important entry leaves, enumerate them and pick one for the trace; summarize the others" would clarify the expected shape.

## Verdict

**Recommend.** The skill produces meaningfully better outputs on all 4 hard codebase-exploration questions (+4.75/25 rubric total), with consistent gains on the substantive criteria (correctness, completeness, structure, actionability) and a tolerable verbosity penalty. The gains are strongest exactly where the skill advertises — execution tracing and abstraction surfacing — and weakest on simpler architecture-mapping questions where the baseline is already competent. Activate for repo onboarding, impact analysis of proposed changes, and "give me the tour" tasks. For pinpoint location queries ("where is function X defined") the baseline is sufficient and the skill is overkill.
