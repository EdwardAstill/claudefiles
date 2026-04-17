# Multi-Agent Coordination

Multi-agent systems (MAS) are the most oversold primitive in the 2024-2026 agent
landscape. They solve a narrow class of problems very well — and fail catastrophically
when applied to anything outside that class. This page catalogues the coordination
patterns, the evidence on when they help, the documented failure modes, and the
implications for agentfiles.

> Cross-reference: `docs/reference/agent-orchestration-patterns.md` (short synthesis
> and routing architectures); `research/harness-foundations.md` (subagent dispatch as
> a harness primitive); `research/context-engineering.md` (subagent context isolation
> as a compaction tool).

---

## 1. The four canonical patterns

Anthropic's "Building Effective Agents" guide and LangGraph's workflow docs converge
on the same four coordination patterns
([LangChain Docs — workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents);
[Arize — Orchestrator-Worker comparison](https://arize.com/blog/orchestrator-worker-agents-a-practical-comparison-of-common-agent-frameworks/)):

| Pattern | Topology | Best for | Key risk |
|---------|----------|----------|----------|
| **Router** | 1 classifier → 1 specialist | Input is heterogeneous, needs different handling | Mis-classification caps quality |
| **Orchestrator-Workers** | 1 orchestrator decomposes → N parallel workers → synthesis | Tasks that genuinely parallelise (e.g. research across independent sources) | Synthesis step is the bottleneck; workers drift from goal |
| **Supervisor (hierarchical)** | 1 supervisor loops among specialists, making routing decisions each turn | Long tasks needing multiple specialists in sequence | Supervisor becomes the bottleneck; fragile to prompt drift |
| **Evaluator-Optimizer** | Generator ↔ Evaluator loop | Quality-critical outputs where iteration improves result | Infinite-loop risk; needs iteration cap |

LangGraph's `Send` API and `create_supervisor` make all four patterns explicit
primitives ([LangChain: langgraph-supervisor-py](https://github.com/langchain-ai/langgraph-supervisor-py)),
which is why it dominates enterprise MAS deployments. AutoGen
([arxiv 2308.08155](https://arxiv.org/abs/2308.08155)) and MetaGPT
([arxiv 2308.00352](https://arxiv.org/abs/2308.00352)) are earlier implementations of
supervisor + role-based patterns respectively.

---

## 2. When multi-agent helps

Multi-agent genuinely outperforms single-agent for:

1. **Embarrassingly parallel research.** N independent sources, each expensive to
   crawl. Orchestrator-worker with fan-out wins on wall-clock time with no quality
   cost.
2. **Role-requiring workflows where roles are cognitively distinct.** ChatDev
   ([arxiv 2307.07924](https://arxiv.org/abs/2307.07924)) and MetaGPT showed
   designer/developer/tester role separation produces better software than a single
   agent juggling all three *when the role prompts are carefully tuned*.
3. **Quality-critical iteration.** Evaluator-optimizer loops produce measurably
   better outputs for translation, writing, and proof-checking — the Self-Refine
   paper showed a consistent ~20% absolute improvement across 7 tasks
   ([Madaan et al., arxiv 2303.17651](https://arxiv.org/abs/2303.17651)).
4. **Context-isolation pressure.** When one sub-task would dominate the main
   context window (e.g. exploring a 200-file codebase), farming it out to a
   subagent returns a compact summary and keeps the main loop lean.

---

## 3. When multi-agent hurts

### The ~15x token tax

Multi-agent systems consume approximately **15x more tokens** than single-agent
systems for the same task, according to Anthropic's production engineering writeup
and multiple practitioner accounts ([Anthropic — Managed Agents](https://www.anthropic.com/engineering/managed-agents);
[truefoundry — Multi Agent Architecture](https://www.truefoundry.com/blog/multi-agent-architecture)).
Every agent must be briefed from scratch, every handoff re-serialises state, and
synthesis does another pass over everything. The tax is real even when the
coordination pattern is "correct".

### DeepMind scaling law: negative returns past an inflection point

The DeepMind paper *Towards a Science of Scaling Agent Systems* (Dec 2025,
[arxiv 2512.08296](https://arxiv.org/abs/2512.08296);
[blog](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/))
measured agent count vs accuracy across tasks. Key findings:

- **For sequential reasoning tasks, adding agents degrades performance by up to
  70%.** Communication overhead disrupts chain-of-thought.
- **Once a single agent reaches ~45% task accuracy, adding agents shows
  diminishing or negative returns.** The coordination tax consumes whatever headroom
  was left.
- Multi-agent wins only for genuinely parallelisable work where tasks have minimal
  inter-dependency.

### LangChain 2025 practitioner data

LangChain's 2025 usage statistics: **73% of production systems are simple chains;
only 12% use full multi-agent** ([State of AI Agents](https://www.langchain.com/stateofaiagents)).
Production teams consistently over-designed upward into MAS, then regressed to
simpler topologies after failures.

---

## 4. The MAST failure taxonomy

Cemri et al. *Why Do Multi-Agent LLM Systems Fail?*
([arxiv 2503.13657](https://arxiv.org/abs/2503.13657), March 2025) analysed 1,600+
traces across 7 MAS frameworks and identified **14 failure modes in 3 categories**:

### Category 1 — System design issues

- Poor agent topology (flat when hierarchy is needed, hierarchy when flat would do)
- Missing error handling at agent boundaries
- Inadequate tool design (tools too coarse, too fine, or ambiguous)
- No re-planning mechanism when execution reveals a flawed plan (static plan-then-execute)

### Category 2 — Inter-agent misalignment (the largest category)

- Agents working at cross purposes due to ambiguous goal decomposition
- Contradictory outputs silently overwriting each other
- Role drift: specialists forgetting their role after many turns
- Goal misalignment compounding turn-over-turn

### Category 3 — Task verification failure

- No mechanism to verify outputs before they return
- Evaluator agent too lenient (rubber-stamping)
- Success criteria undefined or under-specified

**The headline statistic:** Anthropic's review of 200+ enterprise deployments found
**57% of project failures originated in orchestration design**, not model quality.
MAS failures are design failures.

### "Bag of agents" — 17x error amplification

Flat topology with no hierarchy and no verification plane produces up to
**17x error amplification** vs single-agent baselines
([Towards Data Science: 17x Error Trap](https://towardsdatascience.com/why-your-multi-agent-system-is-failing-escaping-the-17x-error-trap-of-the-bag-of-agents/)).
Errors compound because no agent owns the correctness check; everyone assumes
someone else handled it.

---

## 5. Context loss: the #1 named failure mode

Across Anthropic's enterprise analysis, the MAST taxonomy, and multiple practitioner
post-mortems, the single most common failure is **context loss at agent handoff**.
Symptoms:

- Sub-agent doesn't know constraints the main agent already established
- Decisions made by one agent are invisible to the next
- Rework: agent B re-discovers what agent A already found
- Drift: each agent subtly reinterprets the goal until outputs diverge

The mitigation is a structured handoff block (see
[`research/context-engineering.md`](context-engineering.md)) plus an explicit goal
statement that survives every handoff. agentfiles' HANDOFF CONTEXT block is the
current implementation; it should be extended to every subagent dispatch, not just
executor→manager.

---

## 6. Adaptive re-planning

Plans are hypotheses; execution is the experiment. The MAST work, Prompt2DAG
([arxiv 2509.13487](https://arxiv.org/abs/2509.13487)), and the Systematic
Decomposition paper ([arxiv 2510.07772](https://arxiv.org/html/2510.07772v1)) all
argue that **static plan-then-execute is a failure mode, not a virtue**. When an
agent discovers a design flaw mid-execution, pressing on with the original plan
wastes tokens and often ships wrong code.

Adaptive re-planning protocol (synthesised from the three sources):

| Trigger | Response |
|---------|----------|
| Agent fails a task | Analyse why; re-dispatch with augmented context |
| Agent discovers a design flaw | Pause remaining agents; re-evaluate the plan |
| Agent outputs conflict | Linearise the conflicting tasks; re-dispatch serially |
| 3+ agents fail related tasks | Stop — structural problem; re-run the planning phase |

agentfiles' manager already implements Phase 3 (review + replan) along these lines
([`docs/reference/orchestration.md`](../../docs/reference/orchestration.md)), which
is consistent with the literature.

---

## 7. Verification planes

The MAST "task verification" category is preventable with a dedicated verification
step. Patterns that work:

- **Evaluator-optimizer loops** (Self-Refine style): the generator and evaluator
  are explicitly different roles, and the evaluator has well-defined criteria.
- **Deterministic check + model fallback**: run tests and linters first; only
  invoke a model-judge when deterministic checks don't apply.
- **Explicit "verification before completion" step** as a harness gate: the
  agent cannot report success without producing artefact evidence (test output,
  command log). agentfiles codifies this as the `verification-before-completion`
  skill.

---

## Implications for agentfiles

- **The default should remain single-agent.** The executor-first, manager-on-demand
  design is directly validated by the DeepMind scaling study and the LangChain 73%
  statistic. Do not regress to multi-agent defaults under pressure to "scale".
- **Every subagent dispatch needs a HANDOFF CONTEXT block, not just manager ones.**
  Context loss is the most-cited MAS failure; a structured block is the most
  evidence-backed mitigation. Generalise the block template beyond executor→manager.
- **Add an evaluator-optimizer option for quality-critical outputs.** When the task
  is "write a good README / spec / plan", a two-agent loop with a named evaluator
  measurably outperforms single-shot. This is a new skill (or a mode of
  `code-review`), not a default.
- **Document the 15x token tax directly in `manager`'s SKILL.md.** The skill's
  description already gatekeeps manager invocation; citing the number makes the
  gate self-enforcing under pressure.
- **Instrument multi-agent runs specifically.** `af log review` should flag
  sessions where manager was invoked but single-agent would have sufficed — the
  heuristic being agent-count × turn-count / task-complexity. This closes the
  feedback loop on over-routing.
- **Adopt a named verification plane per skill.** Instead of a single
  `verification-before-completion` skill, each specialist (python-expert,
  api-architect, infrastructure-expert) should declare what "verified" means in
  its domain. A lint pass is not verification for a Terraform module; a plan
  + state diff is.
- **Treat 3+ related failures as a structural signal.** The MAST replan protocol
  says to stop and re-plan. Manager's Phase 3 already implements this; the rule
  should be promoted to a hard stop, not a soft suggestion.
