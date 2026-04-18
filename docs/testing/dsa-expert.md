# dsa-expert — Skill Benchmark Report

**Skill:** `agentfiles/coding/dsa/SKILL.md`
**Iteration:** 1
**Workspace:** `tests/dsa-expert/iteration-1/`
**Evals:** 4 LeetCode-Hard–style system-design / DSA problems with reference answers
**Method:** `skill-tester` pipeline — with-skill vs without-skill responses, 5-criterion rubric (Correctness, Completeness, Structure, Clarity, Actionability), graded against reference answers.

## Rubric Scores

| Criterion       | With skill | Without skill | Delta  |
|-----------------|:----------:|:-------------:|:------:|
| Correctness     |    5.00    |     4.00      | +1.00  |
| Completeness    |    5.00    |     3.00      | +2.00  |
| Structure       |    5.00    |     4.00      | +1.00  |
| Clarity         |    4.00    |     5.00      | -1.00  |
| Actionability   |    5.00    |     3.25      | +1.75  |
| **Total / 25**  |  **24.00** |   **19.25**   | **+4.75** |

## Token / Verbosity

Estimated from word count (words × 1.35). Prompt side not counted.

| Metric                         | With skill | Without skill | Delta   |
|--------------------------------|:----------:|:-------------:|:-------:|
| Mean tokens / response         |   1,726    |      590      | +1,136  |
| Tokens per rubric point        |    71.9    |     30.6      | +41.3   |

With-skill responses are about 2.9× longer. That cost buys the +4.75 rubric delta; in terms of marginal tokens per marginal rubric point the ratio is 1,136 / 4.75 ≈ 239 tokens per extra rubric point.

## Per-Eval Breakdown

| Eval                                     | With | Without | Delta | Notes |
|------------------------------------------|:----:|:-------:|:-----:|-------|
| lru-cache-with-ttl                       |  24  |   19    | +5    | With-skill surfaces the version-tombstone trick, evict_lru walking past expired, and sharding; without-skill mentions tombstones in passing. |
| median-in-streaming-data                 |  24  |   19    | +5    | With-skill leads with the bounded-range insight and gives complete median-pointer pseudocode; without-skill leads with two-heaps and treats frequency array as an alternative. |
| concurrent-skip-list-vs-btree            |  24  |   19    | +5    | With-skill gives 6 explicit invariants, full Herlihy-Shavit pseudocode, memory reclamation (EBR vs hazard pointers), and a conditional recommendation. Without-skill is correct but thinner. |
| string-matching-multiple-patterns        |  24  |   20    | +4    | With-skill adds two-tier AC architecture for dynamic updates, sub-ms latency math, NFKC/casefold/Turkish-I pitfall; without-skill is a tighter summary of reference points. |

## Analysis

### What the skill buys

- **Completeness (+2.00).** The skill's prescribed 5-step process forces explicit invariants, trade-off tables, complexity proofs, and edge-case enumeration. Without the skill, responses are correct but treat edge cases as a bullet list rather than a substantive section. This is the largest single contributor to the delta.
- **Actionability (+1.75).** The Step-5 "language handoff" section consistently produces concrete stdlib/library mappings (Python, Rust, Java, Go, C++) and pitfall callouts (Turkish-I case folding, NUMA, heap compaction thresholds). Without-skill responses sometimes omit language handoff entirely.
- **Correctness (+1.00).** The skill's emphasis on invariants and trade-off tables catches subtleties — e.g., version tombstones for heap staleness, evict_lru walking past expired entries — that the without-skill responses glossed over.
- **Structure (+1.00).** Predictable 5-step layout is easier to verify against. The without-skill responses are organized but ad hoc.

### What the skill costs

- **Clarity (-1.00).** With-skill responses are 2.9× longer. Information density is fine, but a reader looking for a quick sketch rather than a production-ready handoff finds the without-skill version faster to scan. This is the one criterion where the skill loses.
- **Token budget.** Roughly 1,136 extra tokens per response. For design questions where a teammate will act on the output, this cost is low-risk (one design doc, used for weeks). For throwaway questions it's overkill.

### Consistency

The +5 / +5 / +5 / +4 eval-level deltas are near-uniform, indicating the gain is not driven by one eval — it reflects the structural process the skill encodes, not topical luck.

### Where the skill could tighten

1. The Step-2 trade-off table is valuable but sometimes redundant with Step-1 constraint discussion. A note saying "skip the table when only one candidate is realistic" would help.
2. Invariants (Step-3) are the highest-leverage part of the process; the skill could explicitly promote them earlier, e.g., "state invariants before pseudocode, not after."
3. The per-language handoff list is heavy — a templated "Python / Rust / Java / one-other" pattern could replace the ad-hoc list that currently produces 4-5 language entries per response.

## Verdict

**Recommend.** The skill produces meaningfully better outputs on 4/4 hard DSA design questions (+4.75 / 25 rubric total), with consistent gains on the substantive criteria (correctness, completeness, actionability) and a tolerable verbosity penalty. Activate for algorithm selection, complexity analysis, and data-structure design tasks. For quick single-complexity answers or refresher Q&A where brevity wins, a user may prefer raw Claude.
