# Self-Improving Agent Systems

The interesting question is not "how good is the agent on turn 1?" but "is turn 1000
better than turn 1?" A **self-improving agent** is one whose behaviour measurably
improves over its operating lifetime without parameter updates — by accumulating
skills, reflecting on failures, rewriting its own prompts, or building external memory.

This page surveys the four architectural families with published evidence of
self-improvement: **reflection** (Reflexion, Self-Refine), **skill accretion** (Voyager),
**social/role-play accumulation** (Generative Agents, ChatDev), and **meta-prompting /
self-editing harnesses** (Anthropic's skills-as-context pattern). It ends with what
an agentfiles self-improvement loop should look like.

> Cross-reference: `research/memory-and-learning.md` for the memory substrate that
> makes accumulation work. `research/context-engineering.md` for the note-taking and
> compaction mechanics that let accumulated knowledge be retrieved on demand.

---

## 1. Reflection and self-critique

### Reflexion (Shinn et al., 2023)

Reflexion introduced "verbal reinforcement learning": after failing a task, the
agent writes a natural-language post-mortem and prepends it to the next attempt's
prompt. No gradients, no reward model — just a persistent self-critique file.
Results: **91% pass@1 on HumanEval vs 80% for GPT-4 without reflection**, plus
consistent gains across decision-making and reasoning benchmarks
([Shinn et al., arxiv 2303.11366](https://arxiv.org/abs/2303.11366)).

Key primitives:
- **Actor** produces outputs
- **Evaluator** (sometimes external tests, sometimes a model) scores them
- **Self-reflector** writes a textual lesson from the failure
- **Memory** persists across attempts

Reflexion's lesson for harness design is structural: **the loop must persist the
reflection text between attempts**, otherwise the "reflection" is a single-turn
trick and nothing accrues.

### Self-Refine (Madaan et al., 2023)

Self-Refine runs feedback→refinement within a single model call chain rather than
across attempts. The same model generates, critiques, and revises. Across 7 tasks
(math, code, dialog), Self-Refine added ~20% absolute quality consistently
([arxiv 2303.17651](https://arxiv.org/abs/2303.17651)). The technique is cheaper
than Reflexion (no external evaluator) but shallower — it doesn't survive across
sessions.

**Design takeaway:** Self-Refine is the right default for quality-critical
*outputs within a session*. Reflexion is the right default for *learning across
sessions*. agentfiles' `code-review` skill and `simplify` skill are Self-Refine in
spirit; the system has nothing Reflexion-shaped yet.

---

## 2. Skill accretion: Voyager

Wang et al.'s **Voyager** ([arxiv 2305.16291](https://arxiv.org/abs/2305.16291)) is
the canonical reference for lifelong learning agents. In Minecraft, Voyager
continuously explores, writes new executable JavaScript skills, and adds them to a
**growing skill library** indexed by semantic embedding of skill descriptions.
Three components drive the loop:

1. **Automatic curriculum** — the agent proposes new tasks that push slightly past
   current capability.
2. **Skill library** — executable code snippets stored with natural-language
   descriptions. Retrieval is by similarity to the current goal.
3. **Iterative prompting with self-verification** — environment errors and
   self-verification drive skill refinement until tests pass.

Voyager outperformed baselines by 3.3x on novel items, 2.3x on unique tech-tree
nodes, and traversed >2x the map distance — all without gradient updates. **The
skill library is the point:** it is the mechanism by which "hours of play" become
"hours of useful memory".

**Mapping to agentfiles:**
The `agentfiles/<category>/<skill>/SKILL.md` pattern is structurally identical to
Voyager's skill library — natural-language retrievable instructions plus optional
executable scripts. What agentfiles currently lacks is the **automatic curriculum
and self-writing loop**. Skills are authored by the human; the system doesn't
propose or draft new skills from observed session patterns.

---

## 3. Social / role-play accumulation

### Generative Agents (Park et al., 2023)

Park et al.'s "Smallville" demonstrated that **observation → reflection →
distillation** loops produce believable long-term behaviour in simulated social
agents ([arxiv 2304.03442](https://arxiv.org/abs/2304.03442)). Every observation
is timestamped, assigned an importance score, and embedded for retrieval. Periodic
reflections cluster related observations into higher-order claims:
*"Klaus spent the whole evening researching, so Klaus is diligent."*
Retrieval scores by weighted sum of recency (exponential decay), relevance
(embedding similarity), and importance.

The contribution to self-improvement literature is the **reflection step**.
Raw logs are too noisy to be useful memory; distilled reflections are what make
behaviour cohere across days. This is Reflexion applied to a social rather than
task-completion setting.

### ChatDev and MetaGPT

ChatDev ([arxiv 2307.07924](https://arxiv.org/abs/2307.07924)) and MetaGPT
([arxiv 2308.00352](https://arxiv.org/abs/2308.00352)) showed that role-specialised
agents producing software in a fixed pipeline (designer → coder → tester → reviewer)
outperform generalist single agents — **when roles are cognitively distinct and
prompts carefully tuned**. The self-improvement angle: the cross-role critique
(tester flags bugs for coder; reviewer flags design issues for designer) functions
as structured feedback that accumulates into better shared docs.

Neither system persists learning across projects by default; the accumulation is
intra-project. This is a gap the literature flags but doesn't solve.

---

## 4. Meta-prompting and self-editing harnesses

### Agent skills as self-modifiable context

Anthropic's agent-skills pattern ([arxiv 2602.12430](https://arxiv.org/html/2602.12430v3);
[Claude API docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview))
is explicitly designed for self-modification: skills are markdown files, the agent
can read them, and with the right tool permissions it can write new ones. The
pattern crossed a practitioner inflection point with `anthropics/skills` reaching
62k+ stars in ~4 months, per the comparative review in
[`research/harness-foundations.md`](harness-foundations.md).

**What this enables in principle:**
- The agent identifies a recurring pattern in session logs.
- It proposes a new skill draft via `writing-skills`.
- The human (or a review agent) approves it.
- Next session, the skill is available via tool-RAG.

This is Voyager's skill library, scaled to coding and with human approval in the
loop.

### Agent S2 and specialist frameworks

Agent S2's "mixture of grounding" showed 18.9% and 32.7% relative improvements from
generalist-specialist routing on desktop tasks
([Agent S2 project page](https://simular.ai/agent-s)). The relevance here is that
**specialisation is a form of self-improvement**: the system gets better as
specialists accrue. But specialisation without a memory substrate plateaus —
specialists need somewhere to store what they learned.

---

## 5. The four-part architecture of genuine self-improvement

Synthesising the above:

```
┌─────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│ Observation │ →  │ Reflection │ →  │ Distilled  │ →  │ Skill /    │
│ (session    │    │ (post-     │    │ artefact   │    │ note /     │
│ logs, tool  │    │ mortem,    │    │ (lesson,   │    │ rule       │
│ results)    │    │ critique)  │    │ pattern)   │    │ update)    │
└─────────────┘    └────────────┘    └────────────┘    └────────────┘
        ▲                                                      │
        └──── retrieved by tool-RAG at relevant moment ────────┘
```

All four steps must exist and persist. Systems that skip observation (Self-Refine)
improve within a session but not across. Systems that skip distillation (raw logs)
drown in noise. Systems that skip artefact promotion (Voyager without the skill
library) can't retrieve what they learned.

**agentfiles status:**
- Observation: session logs and `af log review` exist.
- Reflection: `retrospective` skill exists but must be invoked manually.
- Distillation: no formal mechanism; `observations.md` is a raw summary.
- Artefact promotion: `writing-skills` exists, but no automated bridge.

The gap between steps 3 and 4 is where the self-improvement loop closes — or
doesn't.

---

## 6. Feedback loops and the RL-from-self-play question

True RL-from-self-play with LLM agents (e.g. Eureka-style reward-code generation,
or self-play for code) requires a reliable reward signal and compute budget for
repeated rollouts. For a single-user personal harness, this is out of scope.
What *is* in scope:

- **Periodic reflection on logs** (monthly, or N sessions) to surface recurring
  patterns.
- **Explicit skill proposals** when a pattern crosses a threshold (e.g. three
  sessions with the same workaround).
- **Human-in-the-loop promotion** from lesson → skill draft → reviewed skill.

This trades the full automation of self-play for deterministic improvement with
clear audit trail. For a personal system that values trust and correctness, this
is the correct trade.

---

## Implications for agentfiles

- **Close the observation → artefact loop.** `af log review` produces
  `observations.md`, but there is no automated prompt that says "this pattern has
  appeared 3 times; draft a skill?" Add that prompt as a `retrospective` output
  bullet. This is the Voyager-style skill-accretion step.
- **Add a reflection artefact distinct from raw observations.** Following
  Generative Agents, one layer between raw logs and skill proposals — a
  `research/lessons/<slug>.md` file written by the retrospective skill with
  structured fields (context, pattern, lesson, candidate artefact). The
  `research/lessons/` dir already exists; it needs a templated contribution flow.
- **Formalise the Reflexion-style rewrite for failing skills.** When a skill
  triggers `af log review` warnings (loaded but not used; causing loops), execute
  a structured rewrite step, not a freeform edit. The `writing-skills` skill
  should absorb a Reflexion prompt: "here is the skill, here are the failures,
  produce a corrected version with a rationale."
- **Bias toward Self-Refine for in-session quality.** `code-review` and
  `simplify` already operate this way. Add the pattern explicitly to
  `verification-before-completion`: generate → critique → revise → verify, not
  just verify.
- **Keep the human in the loop on skill promotion.** The literature on unbounded
  self-modification flags drift as the primary risk (MAST "role drift", MAS
  inter-agent misalignment). A personal system should require human approval to
  add or modify skills. The CLI affordance for this should be explicit — e.g.
  `af skill propose <name>` drafting a SKILL.md for review.
- **Track skill-level deltas over time.** To verify self-improvement is actually
  happening, log skill usage, invocation success, and escalation rates per skill
  per month. If the numbers don't trend positive, the loop is cosmetic.
