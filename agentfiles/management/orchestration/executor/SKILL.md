---
name: executor
description: >
  Use at the start of every new task before any other skill. Trigger phrases:
  "can you help me", "I need to", "let's work on", "please do X", "fix this",
  "build X", "investigate Y", "look into Z", "start a new task", "work on this",
  "do the thing", any bare user request with no other skill already loaded.
  Runs orient (af context / af status), makes the routing decision inline, and
  handles the task end-to-end — absorbs specialist skills rather than dispatching.
  Do NOT use when the task genuinely needs parallel multi-domain agents (use
  manager) or when an implementation plan already exists and just needs execution
  (use subagent-driven-development).
---

# Executor

Default agent for all new tasks. Handles everything from a one-liner to a complex
implementation. Makes the routing decision inline — no separate routing step needed.

## Iron Law: Orient before acting

**You cannot make a routing decision — or start any work — without first running:**

```bash
af context   # project fingerprint: name, language, structure
af status    # git state: branch, recent commits, uncommitted changes
```

Skip only if both commands are unavailable (not installed). Skipping because "the task is obvious"
or "you already know the codebase" is not valid — context reveals assumptions you don't know you're making.

## Step 1: Orient and assess

Run `af context` and `af status`. If a `research/knowledge/` exists at the repo
root, also `af ak list` — it prints the distilled agent-knowledge pages that might
already cover the work. Then check for in-progress work artifacts:

- **`docs/specs/*-design.md`** — an existing spec means brainstorming already happened. Don't re-brainstorm; ask if the user wants to resume from the spec.
- **`docs/plans/*.md`** — an existing plan means planning already happened. Offer to execute it (via subagent-driven-development or executing-plans).
- **Feature branch with uncommitted work** — `af status` shows this. Ask if the user wants to continue where they left off.
- **Relevant knowledge pages** — if `af ak list` surfaced a page that looks
  applicable, `af ak show <slug>` before planning. Also scan `research/lessons/`
  — retros there encode past mistakes you should not repeat.

If none of these exist, this is a fresh task. Ask one question:

> **Does this task need multiple agents working in parallel on separate domains?**

**No (the common case) → proceed.** Single agent, any complexity, any depth.
Complex is fine. Many subtasks is fine. Deep domain work is fine.

**Yes → invoke manager.** Only when the task genuinely requires parallel agents
working simultaneously across separate domains, OR scale so large a single context
would degrade (20+ independent subtasks across multiple unrelated areas).

Signals that mean yes:
- User explicitly asks for parallel work ("build X and Y at the same time")
- Multiple codebases or repos involved simultaneously
- Work that truly cannot be sequential

Signals that do NOT mean yes:
- Complex or deep work in one domain
- Many sequential subtasks
- Multiple files in one codebase
- Touching multiple layers (frontend + backend) in the same project

**When in doubt: proceed.** Mid-task escalation is always available if you discover
the scope is larger than expected.

Announce the decision briefly:
```
[single agent — proceeding]   or   [escalating to manager: <one-line reason>]
```

## Step 2: Plan inline (non-trivial tasks only)

**Simple (1–2 clear steps):** Skip planning. Orient and execute directly.

**Non-trivial:** State your approach in 2–4 lines before acting. Enough to avoid
wrong turns — not a full decomposition. Think, then act.

### When to enter Plan Mode first

**Plan Mode is warranted when all three hold:**
1. **Multi-file** — the change touches ≥3 files or spans unrelated layers.
2. **Unfamiliar code** — you haven't traced the relevant modules this session.
3. **Ambiguous approach** — ≥2 reasonable architectures and no signal yet for which.

When any two of those hold, **recommend Plan Mode to the user** rather than
entering it unilaterally — "this looks multi-file with an unclear approach; want
me to switch to Plan Mode first?" Lets the user override if they'd rather see
you dive in.

When none of the three hold, skip Plan Mode — it burns a round-trip for no
benefit.

Source: Anthropic's Claude Code Best Practices — "Explore → Plan → Implement →
Commit" is the default for non-trivial work, but "if the diff fits one sentence,
skip planning."

For larger shapes, consult the task-archetypes registry first. One command:

```bash
af archetype match "<the user's phrasing, quoted>"   # ranked candidates + phase layout
af archetype show <id>                                # full layout for one archetype
af archetype list                                     # all archetype ids
```

If a candidate scores well and fits, lift its phase layout instead of redesigning.
The registry is opinion-encoded; use it.

## Step 3: Execute

**Calibrate effort to the ask.** Before launching research, deep analysis, or
multi-agent work, check whether the user wants a quick answer or a deep dive.
When unclear, ask — one sentence: "Quick overview or deep dive?" Default to the
minimal response that answers the question. Over-delivering wastes tokens and time.

Work through the task with full tool access. When you hit domain-specific work,
load the relevant skill inline:

```
Hit Rust work      → Skill("rust-expert")      → apply patterns in this conversation
Hit API design     → Skill("api-architect")     → apply patterns in this conversation
Need current docs  → Skill("docs-agent")        → look up and continue
Debugging a bug    → Skill("systematic-debugging") → apply in this conversation
```

Inline loading keeps full context throughout. Subagents lose the session; inline keeps it.

### Check the skill's `next:` chain

When you load a skill, read its frontmatter `next:` field (if present). That
lists the skills commonly invoked *after* this one. Queue them mentally as
likely-next steps rather than re-deciding at each transition. Example flow:

```
brainstorming        → next: [writing-plans]
writing-plans        → next: [subagent-driven-development]
subagent-driven-development → next: [verification-before-completion, code-review]
```

`next:` is a hint, not a contract. If the work diverges from the declared
chain, follow the work.

## Step 4: Verify before completion (MANDATORY)

**This step is not optional. Every task exits through verification.**

Before reporting any work as complete, you MUST:

1. **Run the test suite** — if tests exist, run them. Report the output.
2. **Run the code** — if you wrote something executable, execute it and show the output.
3. **Check for regressions** — verify nothing else broke.
4. **Load verification skill** — for non-trivial tasks, `Skill("verification-before-completion")`
   provides the full verification checklist.

**Iron Law:** Do NOT report completion without running verification. A task that
skips verification is not complete — it is a guess.

Evidence means command output, test results, or observable behavior. Phrases like
"should work," "looks correct," or "I believe this is right" are not evidence.

## Step 5: Escalate to manager (when needed)

If at any point during execution you discover the task requires parallel agents
across separate domains, escalate. Include a **HANDOFF CONTEXT** block:

```
## HANDOFF CONTEXT
**Task:** <original user request>
**af context output:** <paste af context output>
**af status output:** <paste af status output>
**Work done so far:** <what you completed before escalating>
**Why escalating:** <specific reason parallelism is needed>
```

This prevents context loss — the #1 failure mode in multi-agent systems.

### Handoff is not just for escalation

Every subagent dispatch — not only executor→manager — loses conversation state.
When you dispatch *any* subagent via the Agent tool, open the prompt with a
compact **CONTEXT** block covering the same structure (task, relevant files,
constraints, files the agent must NOT touch, expected output format). A
subagent with full context produces targeted work; one without it re-explores
from scratch. MAST research attributes ~40% of multi-agent failures to context
loss at handoff boundaries — the mitigation is structural, not optional.

## Anti-loop rules

When loading specialist skills inline, follow these constraints:

1. **Never re-invoke the same skill you are currently inside.** If a skill didn't
   resolve the task, don't reload it — either handle the work directly or escalate.
2. **No backtracking.** Track which skills you've loaded this session. Never route
   back to a skill already visited in the current chain.
3. **Max chain depth: 3.** If you've loaded 3 specialist skills and still haven't
   resolved the task, stop routing and either do the work directly or escalate to
   manager with a HANDOFF CONTEXT block.
4. **If stuck: do the work, don't route.** Routing is not progress. When no
   specialist fits, use your general capabilities rather than hunting for a skill.

## Specialist skills (load inline with Skill tool)

`python-expert` · `typescript-expert` · `rust-expert` · `typst-expert` ·
`api-architect` · `git-expert` · `github-expert` · `github-actions-expert` ·
`tdd` · `systematic-debugging` · `regex-expert` · `verification-before-completion` ·
`docs-agent` · `research-agent` · `codebase-explainer` ·
`security-review` · `database-expert` · `performance-profiling` ·
`infrastructure-expert` · `refactoring-patterns` · `dependency-management` ·
`observability` · `accessibility`

## Verification rationalizations

| Excuse | Reality |
|--------|---------|
| "I manually checked it" | Manual checks miss regressions. Run the suite. |
| "The code is clearly correct" | Correctness is proven by tests passing, not by reading. |
| "No tests exist yet" | Verify with whatever exists: run the code, check the output. |
| "I should escalate to manager to be safe" | Escalate only when parallelism is the actual bottleneck. Complexity alone is not a reason. |
