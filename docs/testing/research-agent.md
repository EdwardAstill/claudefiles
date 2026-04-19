# research-agent — Skill Benchmark Report

**Skill:** `agentfiles/research/research-agent/SKILL.md`
**Iteration:** 1
**Workspace:** `tests/research-agent/iteration-1/`
**Evals:** 4 hard research questions spanning contested empirical literature, industry architecture decisions, language/runtime trade-offs, and supplement-science hype cycles. Each has a documented reference answer.
**Method:** `skill-tester` pipeline — with-skill vs without-skill responses, 5-criterion rubric (Correctness, Completeness, Structure, Clarity, Actionability), graded against reference answers.

## Rubric Scores

| Criterion       | With skill | Without skill | Delta  |
|-----------------|:----------:|:-------------:|:------:|
| Correctness     |    5.00    |     4.75      | +0.25  |
| Completeness    |    5.00    |     3.25      | +1.75  |
| Structure       |    5.00    |     4.00      | +1.00  |
| Clarity         |    4.00    |     5.00      | -1.00  |
| Actionability   |    5.00    |     4.00      | +1.00  |
| **Total / 25**  |  **24.00** |   **21.00**   | **+3.00** |

## Token / Verbosity

Estimated from word count (words × 1.35). Prompt side not counted.

| Metric                         | With skill | Without skill | Delta   |
|--------------------------------|:----------:|:-------------:|:-------:|
| Mean tokens / response         |   1,728    |      848      |  +880   |
| Tokens per rubric point        |    72.0    |     40.4      |  +31.6  |

With-skill responses are about 2.0× longer. On a per-rubric-point basis the multiplier narrows to ~1.8× because the with-skill responses also score higher. The marginal cost per marginal rubric point is 880 / 3.0 ≈ 293 tokens per extra point.

## Per-Eval Breakdown

| Eval                                  | With | Without | Delta | Notes |
|---------------------------------------|:----:|:-------:|:-----:|-------|
| tdd-empirical-evidence                |  24  |   20    | +4    | With-skill wins on completeness — surfaces the 54%/3% SLR overlap figures, 5 enumerated pitfalls, explicit process-conformance critique, and Fucci replication pointer. Without-skill is correct but treats pitfalls as a brief list. |
| microservices-vs-modular-monolith     |  24  |   21    | +3    | With-skill enumerates 10 concrete failure modes (vs without-skill's 10 also but with less explanation each), includes an explicit "ask leadership what pain they're solving" conversation script, and names resume-driven architecture as a flag. Without-skill is a tight correct answer. |
| rust-vs-go-network-services           |  24  |   22    | +2    | Smallest delta. Without-skill already has a clear p99-based decision rule and honest source-quality note. With-skill adds separate "real vs overstated" lists, language-specific failure-mode enumerations, and confidence tiers. |
| creatine-cognition-healthy-adults     |  24  |   21    | +3    | With-skill provides concrete self-trial protocol (dose, duration, specific test), 6 enumerated pitfalls, effect-size comparison with caffeine, and dose/timing nuances. Without-skill has the key EFSA-2024 critique and population-dependent framing but less operational detail. |

## Analysis

### What the skill buys

- **Completeness (+1.75).** The largest driver of the delta. The skill's prescribed output format (Consensus / Nuances / Known Pitfalls / Contradictions / Recommended Direction / Further Investigation) forces explicit coverage of dimensions that raw Claude answers in passing or omits. Particularly valuable for the TDD and creatine questions where the literature is contested — the without-skill responses get the main claims right but don't enumerate failure modes or differentiate confidence tiers per claim.
- **Structure (+1.00).** The claim-type audit table and tiered confidence summary are the two layers that most consistently separate with-skill from without-skill. They make the reasoning easier to verify and easier to cite. The without-skill responses are organized, but ad-hoc.
- **Actionability (+1.00).** The skill's "Further Investigation" section consistently produces concrete next steps — specific papers with identifiers, measurement protocols, self-trial designs, conversation scripts for pushing back to leadership. Without-skill responses often name references but don't package them into a do-next list.

### What the skill costs

- **Clarity (-1.00).** With-skill responses are 2.0× longer. For a reader who just wants a quick answer, the without-skill version is tighter, scannable, and arrives at the recommendation faster. The without-skill creatine and microservices responses in particular read as cleanly-edited summaries; the with-skill versions require focused reading.
- **Token budget.** ~880 extra tokens per response. For a question that will inform a multi-stakeholder decision (mandating TDD, defending against a premature microservices migration, choosing a language for a multi-year project) this cost is trivially justified. For a quick "what does the research say" question it's overhead.

### Correctness barely separates (+0.25)

This is interesting. On these questions — drawing on well-documented contested literatures — raw Claude with web search gets the main facts right. The without-skill responses correctly cited EFSA 2024, the SLR overlap, Discord's migration, Amazon Prime Video, and so on. The separation between with-skill and without-skill is **not** "one is factually wrong and one isn't" — it's "one makes the reasoning auditable and the other doesn't." For a skill explicitly about cross-source weighting and contested claims, this is the right criterion to shine on, and it does (via completeness and structure).

### Consistency

The per-eval deltas are +4 / +3 / +2 / +3, all positive but smaller than the dsa-expert baseline (which was +5 / +5 / +5 / +4). The smallest delta (Rust vs Go) is the question where the without-skill baseline already has a clear mechanistic decision rule available from the model's training data. The largest delta (TDD) is the question with the messiest literature, where the skill's insistence on claim-type audit and confidence tiering pays off most. This pattern is consistent with the skill's stated value proposition: it matters more as evidence gets messier.

### Where the skill could tighten

1. **Claim-type audit is valuable but repetitive in the "Consensus" block that follows.** The same claims get re-labeled "strong consensus / moderate / contested" in two places. A single pass would save ~100 tokens without losing rigor.
2. **"Source Quality Note" sections are sometimes skipped** (it appears in Rust-vs-Go and Microservices but not TDD or Creatine in this run). The skill should make this a required subsection when the user is asking about contested or marketing-heavy domains.
3. **The "Depth calibration" preface is noise for a single-turn benchmark run.** In a real session it's a useful defensive check; in one-shot research it costs clarity. A shorter version — one sentence offering to go deeper if asked — would be enough.
4. **Per-population / per-context recommendations are the highest-value part of the "Recommended Direction" section** (vegetarian vs omnivore for creatine; sub-ms vs 5-50ms p99 for Rust vs Go; 30 vs 100 engineers for microservices). The skill could promote these to a dedicated "if you are X then Y" block rather than burying them in prose.

## Verdict

**Recommend.** The skill produces meaningfully better outputs on 4/4 hard research questions (+3.00 / 25), with consistent gains on the substantive criteria that matter for this skill's use case (completeness, structure, actionability). The -1.00 clarity penalty reflects real verbosity cost and is worth acknowledging. Correctness separates only modestly (+0.25) because raw Claude with web search handles these questions capably on the facts; the skill's value is in the auditable reasoning structure, not fact retrieval.

Activate the skill when:
- the question involves **contested empirical evidence** (consensus is not obvious),
- the output will be **forwarded or cited** (e.g., tech lead relaying to leadership, engineer defending a language choice to a skeptical team),
- the user needs **multi-population / multi-context recommendations** rather than a single answer,
- the user explicitly asks about **trade-offs, failure modes, or risks** (the skill's trigger phrases).

For quick one-shot research questions where the user just needs a correct summary, raw Claude is tight, fast, and sufficient.
