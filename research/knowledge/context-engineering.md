---
id: K-001
---

# Context Engineering

Prompt engineering was about picking the right words. **Context engineering** is about
deciding what text is in the model's working buffer at each step, how it got there,
and how long it stays. Anthropic framed the shift in September 2025: *"context is a
finite resource with diminishing marginal returns"*, and the engineering goal is to
find the smallest set of high-signal tokens that maximise the likelihood of the
desired outcome
([Anthropic, 2025](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)).

This page catalogues the techniques production systems use to keep the context window
useful across long sessions: lazy skill loading (tool-RAG), compaction, structured
note-taking, handoff blocks, and session resumption. It ends with the implications
for agentfiles — some of which we already do, some we should.

> Cross-reference: `research/harness-foundations.md` (context window as a primitive);
> `research/memory-and-learning.md` (what persists *outside* the context window).

---

## 1. The binding constraint

Even with a 1M-token window, **attention is not uniform across the buffer**. Anthropic
and third-party evaluations report a "context rot" curve: factual recall, instruction
following, and tool selection all degrade as the buffer fills with marginally
relevant tokens ([Inkeep: Fighting Context Rot](https://inkeep.com/blog/fighting-context-rot);
[HowAIWorks: Context Engineering](https://howaiworks.ai/blog/anthropic-context-engineering-for-agents)).
Tool-selection accuracy in particular falls off rapidly as tool count and irrelevant
history grow ([RAG-MCP, arxiv 2505.03275](https://arxiv.org/abs/2505.03275)).

The practical consequence: **"put it in the prompt" is not a scalable mitigation for
agent knowledge gaps.** Every token added to a default prompt is a token's worth of
attention removed from whatever the user actually asked.

---

## 2. Lazy skill loading = tool-RAG for instructions

RAG-MCP (Gan & Sun, May 2025) showed that selecting ~3 relevant tools via semantic
retrieval, rather than presenting all 11,100 in the benchmark pool, **tripled
tool-invocation accuracy while cutting prompt tokens by 50%**
([arxiv 2505.03275](https://arxiv.org/abs/2505.03275)). The same logic applies to
skills. When a harness shows only skill *names and descriptions* at session start and
loads the full body on demand, the context tax per skill drops from kilobytes to tens
of bytes.

The formalised definition of an **agent skill** — a bundle of instructions, scripts,
reference docs, and metadata dynamically retrievable by the agent — was articulated
in [arxiv 2602.12430](https://arxiv.org/html/2602.12430v3) and is the pattern Claude
Code implements with `SKILL.md` files. Adoption data: `anthropics/skills` reached
62k+ GitHub stars within four months of release, indicating the tool-RAG-for-prompts
pattern crossed a practitioner inflection point.

**Why it works:**
- Skill bodies can be arbitrarily long (workflows, examples, scripts) without taxing
  the default context.
- The router only needs to distinguish between descriptions — a much easier problem
  than routing on full skill bodies.
- Skills compose: a single task can pull in multiple skills by loading them in
  sequence, each at its point of need.

**Where it fails:**
- When descriptions are indistinct, the router picks wrong or loads duplicates. The
  MAST paper's "inter-agent misalignment" category subsumes this on the multi-agent
  side ([Cemri et al., arxiv 2503.13657](https://arxiv.org/abs/2503.13657)).
- Skills that load other skills can cascade; each load is a round-trip and adds
  tokens. 30-40 well-distinguished skills is a practical ceiling for a single
  orchestrator before routing breaks down.

---

## 3. Compaction

Compaction replaces earlier conversation turns with a model-generated summary when
the buffer nears its limit. Anthropic describes three variants in the 2025 guide
([link](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)):

| Variant | How it works | When to use |
|---------|-------------|-------------|
| **Full compaction** | Summarise the whole transcript into one block | Long sessions, model hitting 95%+ fill |
| **Tool-result clearing** | Keep the tool call, drop the verbose output | Safest; most recently shipped on the Claude Developer Platform |
| **Selective compaction** | Rewrite specific spans (e.g. old searches) while keeping recent code edits intact | Mixed-task sessions |

Claude Code auto-compacts at ~98% of the context budget
([Claude Code Docs](https://code.claude.com/docs/en/how-claude-code-works)).
Critical metadata (file list, plan state) is preserved; images and PDFs are stripped.

**Key operational insight:** compaction is a controlled quality trade. The summary
is lossier than the original, so the system should compact only *older* material
the agent is unlikely to re-use. Premature compaction is as bad as no compaction —
both lose information the task still needs.

---

## 4. Structured note-taking (agentic memory)

Anthropic's guide elevates **structured note-taking** — writing persistent notes to
disk *outside* the context window and reading them back on demand — as a first-class
context-engineering technique. The pattern:

1. Agent does work; takes notes into a known file (`NOTES.md`, `memory.md`,
   `.agentfiles/notes.md`).
2. When the buffer fills or a session ends, the conversation is compacted, but the
   notes persist.
3. Next time the relevant topic arises, the agent reads the notes back into context.

MemGPT formalised this with an OS-inspired paging scheme: main context is RAM,
external memory is disk, and the model learns to `read`/`write`/`search` between
them ([Packer et al., arxiv 2310.08560](https://arxiv.org/abs/2310.08560)). The
Claude Cookbook's context engineering recipe shows the minimum-viable version: a
single shared file the agent agrees to maintain
([Claude Cookbook](https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools)).

This is also where agent-memory taxonomies land: episodic (what happened), semantic
(what is true), procedural (how to do X). The memory-and-learning page goes deeper
on retrieval strategies. The context-engineering point here is that **notes are a
compaction alternative that does not lose information** — they move it outside the
buffer rather than summarising it away.

---

## 5. Handoff blocks and session resumption

Long tasks inevitably cross session boundaries. The failure mode is **context loss
at handoff**, named the #1 failure of multi-agent systems in Anthropic's analysis
of 200+ enterprise deployments and the MAST taxonomy alike.

The mitigation is a **structured handoff block**: a canonical document containing

- Current goal and sub-goals
- Work completed with file paths and test outcomes
- Open decisions and their current lean
- Immediate next action for the incoming agent
- Reference pointers (URLs, paper slugs, relevant skill names)

agentfiles' executor already emits a HANDOFF CONTEXT block when escalating to
manager ([`docs/reference/orchestration.md`](../../docs/reference/orchestration.md)).
The pattern is worth generalising: a session-end handoff file (`.agentfiles/handoff.md`)
that a later session can read to resume without replaying the full transcript.

Session resumption in Claude Code specifically uses the `--resume` / `--continue`
flags plus saved history JSON. Anthropic's advice on long-running agents is to treat
the transcript as untrusted input: always re-read the plan file and the code, never
rely on the transcript alone ([Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)).

---

## 6. Sub-agent isolation as a context-engineering tool

Spawning a subagent with a fresh context is itself a compaction strategy:
expensive-to-reconstruct work (e.g. reading 50 files to summarise a codebase) runs
in the subagent, and only the final summary returns to the main loop. Anthropic
calls this the third pillar of context engineering alongside compaction and notes.

The trade-off is clear: subagents lose conversational context. For exploration and
research they win (pure information gathering). For tightly-coupled engineering
work they lose (main-loop already holds the relevant state). This underlies
agentfiles' "default to inline skills, escalate to subagents only when genuinely
parallel" rule.

---

## Implications for agentfiles

- **Keep skill descriptions pathologically distinct.** Descriptions are the
  tool-RAG index. `af check` already validates existence; add a similarity check
  that flags skills whose descriptions share > N-gram overlap above threshold.
  RAG-MCP's accuracy-tripling result is entirely about distinguishability.
- **Formalise `.agentfiles/notes.md` as the structured-note-taking channel.** It
  already exists via `af note`. Prompt executor (in `SKILL.md`) to append findings
  there at natural checkpoints, not just on demand. This turns a one-off CLI into
  a compaction-resistant memory.
- **Add a session-end handoff artefact.** `af note --handoff` (or similar) writes
  a templated `.agentfiles/handoff.md` so the next session starts with plan state,
  not a replay. The HANDOFF CONTEXT block exists for executor→manager; extend it
  to session→session.
- **Monitor context fill, don't assume the model will.** Hook into
  `UserPromptSubmit` to warn when context utilisation exceeds a threshold (e.g.
  70%) and suggest compaction, note-taking, or a subagent handoff. This is the
  direct implementation of Anthropic's "attention budget" principle.
- **Bias subagent dispatch toward read-only exploration.** Research, codebase
  exploration, and docs lookup are ideal subagent workloads: they return compact
  summaries and benefit from context isolation. Coding work is not — it benefits
  from inline state. The rule should be stated explicitly in `manager`'s SKILL.md.
- **Treat `CLAUDE.md` as attention-budget debt.** Every line is a tax on every
  turn. Audit periodically; move anything conditional into a skill that loads only
  when relevant.
