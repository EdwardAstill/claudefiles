# Memory and Learning Across Sessions

An agent without memory is a translator: every turn begins from zero. A personal
assistant without memory is a stranger each morning. The agent-memory literature
distinguishes between three storage substrates and at least four retrieval
strategies, and gives specific guidance on how a single-user system should wire
them together so that each session starts smarter than the last.

This page catalogues the memory taxonomies, the retrieval mechanics, and the
observation → reflection → distillation loop that turns raw logs into usable
knowledge. It closes with implications for how agentfiles should persist learning
in a single-user personal system.

> Cross-reference: `research/self-improving-agents.md` (what the memory is for —
> the improvement loop it feeds). `research/context-engineering.md` (structured
> note-taking as the bridge between memory and the context window).

---

## 1. Memory taxonomy

Production agent-memory architectures converge on three long-term types borrowed
from cognitive psychology, plus short-term working memory
([MongoDB — Agent Memory](https://www.mongodb.com/resources/basics/artificial-intelligence/agent-memory);
[IBM — AI Agent Memory](https://www.ibm.com/think/topics/ai-agent-memory);
[Redis — Agent Memory Architecture](https://redis.io/blog/ai-agent-memory-stateful-systems/);
[MachineLearningMastery — 3 Long-term Memory Types](https://machinelearningmastery.com/beyond-short-term-memory-the-3-types-of-long-term-memory-ai-agents-need/)):

| Type | Stores | Example | Retrieval |
|------|--------|---------|-----------|
| **Working / short-term** | Current context window | Active task, last few turns | Attention |
| **Episodic** | What happened — events, interactions, outcomes with timestamps | "On 2025-03-14 the user asked about Stow; I explained X; it worked" | Vector similarity over event embeddings |
| **Semantic** | What is true — facts, relationships, concepts | "User prefers `uv` over `pip`. Project X uses Hyprland on Wayland." | Fact lookup, knowledge graph |
| **Procedural** | How to do X — multi-step know-how | "To deploy, build → migrate → swap traffic. To debug Y, check Z first." | Keyword / semantic on procedure descriptions |

A robust production agent uses all four. Omitting one produces characteristic
failure modes:

- No episodic → forgets that the user has already been told something
- No semantic → re-derives known facts every session
- No procedural → repeats the same slow workflow inefficiently
- No working → can't hold a thought across two turns

For a **single-user personal system**, the priority ordering is roughly:
procedural > semantic > episodic. Personal productivity tools benefit most from
accurate "how I do X" knowledge, then from stable "what is true about my setup",
and last from exhaustive "what have we discussed". Enterprise chat agents invert
this.

---

## 2. Storage substrates

The agent-memory survey *Memory for Autonomous LLM Agents: Mechanisms, Evaluation,
and Emerging Frontiers* ([arxiv 2603.07670](https://arxiv.org/html/2603.07670v1))
and TechRxiv's *Memory in LLM-based Multi-agent Systems*
([preprint](https://www.techrxiv.org/users/1007269/articles/1367390/master/file/data/LLM_MAS_Memory_Survey_preprint_/LLM_MAS_Memory_Survey_preprint_.pdf?inline=true))
catalogue four storage approaches:

| Substrate | Strengths | Weaknesses |
|-----------|-----------|------------|
| **Flat markdown / notes** | Human-readable; trivial to edit; version-controllable | No retrieval scaling past a few MB |
| **Vector database** | Semantic retrieval across many embeddings | Opaque; retrieval quality depends on chunking |
| **Knowledge graph** | Precise relational queries; supports reasoning | Extraction is expensive; schema rigidity |
| **Hybrid (MemGPT-style paging)** | Combines paging (compaction) with explicit memory tools | Implementation complexity |

MemGPT ([Packer et al., arxiv 2310.08560](https://arxiv.org/abs/2310.08560))
formalised the OS-inspired paging model: main context is RAM; external store is
disk; the model calls `read`/`write`/`search` tools to move pages between them.
This decouples storage size from context size.

**For a single-user personal system**, flat markdown indexed by filename and full-text
search is a surprisingly high ceiling. A `wiki/` directory plus `ripgrep` plus a
disciplined filename convention gets most of the way to semantic retrieval without
an embedding pipeline. agentfiles currently works this way (`.agentfiles/notes.md`,
skill SKILL.md files). A vector index would add recall, not architecture.

---

## 3. The retrieval problem

Retrieval is the part most systems get wrong. Three decisions:

### What to index

- **Raw event stream** — every observation, every tool call. High recall, low
  signal. Search returns too much noise.
- **Distilled artefacts** — reflections, lessons, summaries. High signal, lower
  recall (if you didn't distill the right thing, you can't find it).
- **Both, with tiered retrieval** — query the distilled artefacts first; fall
  back to the raw stream if needed. This is what Generative Agents
  ([arxiv 2304.03442](https://arxiv.org/abs/2304.03442)) does.

### How to score

Generative Agents' scoring function is the widely-cited baseline:

```
retrieval_score = α · recency + β · relevance + γ · importance
```

- **Recency**: exponential decay on elapsed time (memories get "colder")
- **Relevance**: cosine similarity between query embedding and memory embedding
- **Importance**: self-assessed 1-10 score at write time (is this mundane or
  pivotal?)

For a personal system, recency decay should be slow (user preferences remain
stable for months), and importance should be biased by authorship: notes the
user wrote are likely higher-signal than notes the agent wrote.

### When to retrieve

- **On every turn** → expensive, context-polluting, often irrelevant.
- **On tool-RAG trigger** → retrieve when a skill needs domain memory.
  Scales well.
- **On explicit command** (`af note --read`, `knowledge-base` skill) → user
  controls. Most predictable.

agentfiles currently uses the explicit-command pattern (`af note --read`,
`af read`). The implicit tool-RAG pattern would be an upgrade for skills like
`knowledge-base` that should pull context without user prompting.

---

## 4. Observation → reflection → distillation

This is the core learning loop for any long-running agent system. Raw logs are
too noisy for retrieval; distilled lessons are what make knowledge compound
across sessions.

### Stage 1 — Observation capture

Every session produces:
- Tool calls and their results
- Decisions made and their rationales
- User feedback and corrections
- Errors and recoveries

agentfiles captures these via hooks into session logs. This is the raw stream.
It is useful for `af log review` but should not be the retrieval substrate
directly.

### Stage 2 — Reflection (the crucial step)

Reflection clusters related observations and writes higher-order claims.
Generative Agents reflect periodically on importance-weighted clusters;
Reflexion reflects after failures; the Anthropic skills pattern reflects
after a skill is loaded repeatedly without being used.

For agentfiles, the `retrospective` skill is the reflection mechanism. Its
output is currently raw (`observations.md`). The upgrade is to move from
"list of observations" to "list of claims with supporting evidence":

```
CLAIM: systematic-debugging triggers too eagerly on known-fixed issues
EVIDENCE: sessions 2025-03-14, 2025-03-19, 2025-03-22 all showed skill
  loaded and immediately exited when issue was trivial
PROPOSED ACTION: tighten skill description to exclude "simple" cases
```

### Stage 3 — Distillation into artefacts

A reflection only becomes useful memory when it becomes a *retrievable artefact*.
For agentfiles, the artefacts are:

- **`wiki/lessons-learned/<slug>.md`** — short notes with context, lesson,
  citation. Versioned; human-readable; grep-able.
- **`SKILL.md` edits** — when a lesson crosses a threshold (repeated pattern),
  it becomes a skill-level rule.
- **`CLAUDE.md` / `AGENTS.md` updates** — when a lesson is broadly applicable,
  it becomes top-level guidance.

The transitions up this hierarchy are the value. A system that only writes
lessons (but never promotes to skills) learns the same thing every month.

---

## 5. Personal-system specific considerations

The papers mostly target enterprise or research settings (many users, shared
memory, access control). A single-user personal system has different economics:

1. **No multi-tenant concerns.** The agent can assume continuity of user and
   project context.
2. **Very long session horizons.** Sessions weeks apart should still share
   memory. Enterprise chatbots often reset per-conversation.
3. **High tolerance for human review.** The user is there and can approve
   memory writes. Trust-sensitive; privacy-trivial.
4. **Small data, high signal.** Hundreds of sessions, not millions. Flat files
   beat vector DBs at this scale.
5. **Version control is free.** `git` already tracks change history; no need
   for a separate memory provenance system.

**Implication:** the memory architecture for a personal agent looks more like
a structured wiki than a database. Markdown files + filename conventions +
git + grep is the starting design. Add vectors only when grep plateaus.

---

## 6. Retrieval strategies specific to agentfiles

| Source | How agent retrieves | Current status |
|--------|--------------------|----------------|
| **Skill descriptions** | Tool-RAG via Skill tool at session start | Implemented |
| **`CLAUDE.md` / `AGENTS.md`** | Injected on every turn (top of context) | Implemented; risks attention-budget debt |
| **`.agentfiles/notes.md`** | Explicit via `af note --read` | Implemented; not auto-surfaced |
| **`wiki/research/*.md`** | Manual reference by agents consulting design decisions | Created this pass |
| **`wiki/lessons-learned/`** | Manual reference during retrospective + design | Scaffolded; needs contribution flow |
| **`knowledge-base` skill** | Full-text search of personal knowledge base | Implemented for health/training domain |

The gap: **no automatic retrieval of lessons-learned during task execution.** A
lesson about "always run `af check` before committing skill changes" is useful
only if the agent sees it at the moment it's about to commit. The existing
knowledge-base skill pattern is the model — extend it to the meta-domain
(skill and harness lessons).

---

## Implications for agentfiles

- **Adopt the three-type taxonomy explicitly.** `AGENTS.md` = procedural
  (how-we-work rules); `wiki/research/` = semantic (what we've concluded);
  `wiki/lessons-learned/` + session logs = episodic. Document the mapping in
  `AGENTS.md` so future skills respect the separation.
- **Promote lessons to artefacts on a cadence, not ad hoc.** Schedule
  `retrospective` monthly (or after every N sessions). Require its output to
  propose at least one promotion: lesson → skill edit, or observation → lesson.
  If nothing is worth promoting, record that too — learning has a signal.
- **Implement importance scoring for `af note`.** A flag like
  `af note --importance high "finding"` biases future retrieval. Default
  to medium. The Generative Agents scoring is over-engineered for a personal
  system; a 3-level tag is enough.
- **Use recency for noise reduction, not just ordering.** Lessons older than
  six months without reinforcement should be marked dormant rather than deleted
  — preserves history while de-prioritising retrieval.
- **Keep memory in the wiki, not a vector DB.** At personal-system scale, flat
  markdown + grep dominates. Add embeddings only if a specific skill (e.g.
  `knowledge-base`) demonstrates grep is insufficient.
- **Bind memory to the reflection loop, not the tool loop.** Reading memory
  on every turn is the wrong default (pollutes context). Reading memory when
  a skill explicitly asks ("given this task, retrieve relevant lessons") is
  the right default. Today the path is `af wiki list` to surface candidates
  plus `rg wiki/lessons-learned/` for full-text — no dedicated CLI needed
  until grep plateaus.
- **Keep the lesson-file template in `wiki/lessons-learned/README.md`, not in
  a CLI scaffolder.** A previous `af lessons new` scaffolder was reverted as
  bloat: `touch wiki/lessons-learned/<YYYY-MM-DD-slug>.md` plus the README
  template is enough. Add a scaffolder only if filename or field drift
  becomes a measured problem.
